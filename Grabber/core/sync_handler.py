from pyrogram import filters, ContinuePropagation
from Grabber import app, game_bot
from Grabber.database import user_collection, r
import logging
import asyncio

LOGGER = logging.getLogger(__name__)

async def sync_user_data(message):
    """Update user first name and username in the database periodically."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    cache_key = f"sync:{user_id}"
    if r:
        if await r.get(cache_key):
            return
        await r.setex(cache_key, 3600, "1")  # Sync once an hour

    try:
        await user_collection.update_many(
            {"id": {"$in": [user_id, str(user_id)]}},
            {"$set": {"first_name": first_name, "username": username}}
        )
    except Exception as e:
        LOGGER.error(f"Failed to sync user data for {user_id}: {e}")

@app.on_message(filters.regex(r"^/"), group=-20)
async def app_sync_user(client, message):
    """Handler for MainBot to trigger user data sync on commands."""
    raise ContinuePropagation
    asyncio.create_task(sync_user_data(message))

@game_bot.on_message(filters.regex(r"^/"), group=-20)
async def game_bot_sync_user(client, message):
    """Handler for GameBot to trigger user data sync on commands."""
    raise ContinuePropagation
    asyncio.create_task(sync_user_data(message))
