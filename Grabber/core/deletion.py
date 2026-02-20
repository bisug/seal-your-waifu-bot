import asyncio
import time
from pyrogram import types, errors
from Grabber.database import deletion_queue_collection
from Grabber import app, LOGGER

async def schedule_deletion(chat_id: int, message_id: int, delay: int = 300):
    """
    Saves a message to the persistent deletion queue in MongoDB.
    :param chat_id: The ID of the chat where the message exists.
    :param message_id: The ID of the message to delete.
    :param delay: Time in seconds to wait before deletion (default 5 mins).
    """
    delete_at = time.time() + delay
    await deletion_queue_collection.insert_one({
        "chat_id": chat_id,
        "message_id": message_id,
        "delete_at": delete_at
    })
    LOGGER.info(f"Scheduled persistent deletion for message {message_id} in {chat_id} at {delete_at}")

async def deletion_worker():
    """
    Background worker that checks the MongoDB deletion queue every 60 seconds
    and deletes expired messages.
    """
    LOGGER.info("Persistent Deletion Worker started.")
    while True:
        try:
            now = time.time()
            # Find messages where delete_at is less than or equal to current time
            cursor = deletion_queue_collection.find({"delete_at": {"$lte": now}})
            expired_messages = await cursor.to_list(length=100)
            
            for msg in expired_messages:
                chat_id = msg["chat_id"]
                message_id = msg["message_id"]
                
                try:
                    await app.delete_messages(chat_id, message_id)
                except errors.Forbidden:
                    LOGGER.warning(f"Could not delete message {message_id} in {chat_id}: Forbidden (Bot not admin?)")
                except errors.MessageDeleteForbidden:
                    LOGGER.warning(f"Could not delete message {message_id} in {chat_id}: Not allowed to delete.")
                except Exception as e:
                    # Message might already be deleted or other error
                    pass
                
                # Remove from queue regardless of success (to prevent retrying forever)
                await deletion_queue_collection.delete_one({"_id": msg["_id"]})
                
        except Exception as e:
            LOGGER.error(f"Error in deletion_worker loop: {e}")
            
        await asyncio.sleep(60)
