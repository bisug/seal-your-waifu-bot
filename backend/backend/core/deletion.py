import asyncio
import time
from pyrogram import errors
from pyrogram.errors import FloodWait
from backend import LOGGER, app, game_bot
from backend.database import deletion_queue_collection
async def schedule_deletion(chat_id: int, message_id: int, delay: int = 300, bot_name: str = "MainBot"):
    """
    Saves a message to the persistent deletion queue in MongoDB.
    :param chat_id: The ID of the chat where the message exists.
    :param message_id: The ID of the message to delete.
    :param delay: Time in seconds to wait before deletion (default 5 mins).
    :param bot_name: Which bot sent the message — 'MainBot' or 'GameBot'.
    """
    delete_at = time.time() + delay
    await deletion_queue_collection.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_at": delete_at,
        "bot_name": bot_name
    })
async def deletion_worker():
    """
    Background worker that checks the MongoDB deletion queue every 60 seconds
    and deletes expired messages using the correct bot client.
    OPTIMIZED: Groups messages by chat_id for batch deletion (up to 100 per API call)
    to stay well within Telegram's rate limits.
    """
    LOGGER.info("Persistent Deletion Worker started.")
    while True:
        try:
            from collections import defaultdict
            now = time.time()
            cursor = deletion_queue_collection.find({"delete_at": {"$lte": now}})
            expired_messages = await cursor.to_list(length=100)
            # Group by (chat_id, bot_name) so we can batch-delete per chat
            batches = defaultdict(list)
            for msg in expired_messages:
                key = (msg["chat_id"], msg.get("bot_name", "MainBot"))
                batches[key].append(msg)
            processed_ids = []
            for (chat_id, bot_name), msgs in batches.items():
                client = game_bot if bot_name == "GameBot" else app
                msg_ids = [m["message_id"] for m in msgs]
                try:
                    # Single batch API call per chat (Telegram supports up to 100 at once)
                    await client.delete_messages(chat_id, msg_ids)
                    await asyncio.sleep(0.05)  # 50ms gap between chats to pace API usage
                except FloodWait as e:
                    LOGGER.warning(f"FloodWait {e.value}s during deletion for {chat_id}, skipping batch this cycle")
                    continue  # Skip — these will be retried next cycle
                except (errors.Forbidden, errors.MessageDeleteForbidden, errors.Unauthorized):
                    pass  # No delete permission — still mark as processed to avoid infinite retry
                except errors.SlowmodeWait as e:
                    LOGGER.warning(f"SlowmodeWait {e.value}s during deletion in {chat_id}")
                    await asyncio.sleep(e.value)
                    continue  # Skip marking as processed, retry next cycle
                except errors.MessageIdsEmpty:
                    pass  # Kurigram 2.2.25: typed replacement for MESSAGE_ID_INVALID — mark as processed
                except errors.BadRequest as e:
                    if "MESSAGE_ID_INVALID" in str(e) or "CHAT_ID_INVALID" in str(e):
                        pass # Mark as processed
                    else:
                        LOGGER.debug(f"BadRequest in deletion batch {chat_id}: {e}")
                except Exception as e:
                    LOGGER.debug(f"Failed to delete batch in {chat_id}: {e}")
                processed_ids.extend([m["_id"] for m in msgs])
            # Single bulk delete for all processed entries
            if processed_ids:
                await deletion_queue_collection.delete_many({"_id": {"$in": processed_ids}})
        except Exception as e:
            LOGGER.error(f"Error in deletion_worker loop: {e}")
        await asyncio.sleep(60)
