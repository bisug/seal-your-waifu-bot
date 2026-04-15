import asyncio
import time

from pyrogram import errors

from Grabber import LOGGER, app, game_bot
from Grabber.database import deletion_queue_collection


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
    Processed entries are removed in a single bulk delete_many call.
    """
    LOGGER.info("Persistent Deletion Worker started.")
    while True:
        try:
            now = time.time()
            cursor = deletion_queue_collection.find({"delete_at": {"$lte": now}})
            expired_messages = await cursor.to_list(length=100)

            processed_ids = []
            for msg in expired_messages:
                chat_id = msg["chat_id"]
                message_id = msg["message_id"]
                client = game_bot if msg.get("bot_name") == "GameBot" else app

                try:
                    await client.delete_messages(chat_id, message_id)
                except (errors.Forbidden, errors.MessageDeleteForbidden):
                    pass
                except Exception as e:
                    LOGGER.debug(f"Failed to delete old message {message_id}: {e}")

                processed_ids.append(msg["_id"])

            # Single bulk delete for all processed entries
            if processed_ids:
                await deletion_queue_collection.delete_many({"_id": {"$in": processed_ids}})

        except Exception as e:
            LOGGER.error(f"Error in deletion_worker loop: {e}")

        await asyncio.sleep(60)
