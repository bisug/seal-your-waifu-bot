import asyncio
import logging
from pyrogram import ContinuePropagation, enums, errors, filters, types

from Grabber import app, game_bot
from Grabber.database import r, user_collection
LOGGER = logging.getLogger(__name__)

async def sync_user_data(message):
    """Update user first name and username in the database periodically."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    # Don't overwrite with empty name
    if not first_name:
        return
    cache_key = f"sync:{user_id}"
    if r:
        if await r.get(cache_key):
            return
        await r.setex(cache_key, 1800, "1")  # Sync once every 30 minutes
    try:
        await user_collection.update_many(
            {"id": {"$in": [user_id, str(user_id)]}},
            {"$set": {
                "first_name": first_name,
                "last_name": last_name,
                "username": username
            }}
        )
    except Exception as e:
        LOGGER.error(f"Failed to sync user data for {user_id}: {e}")

@app.on_message(~filters.bot, group=-20)
async def app_sync_user(client, message):
    """Handler for MainBot to trigger user data sync on every user message."""
    if message.from_user:
        asyncio.create_task(sync_user_data(message))
    raise ContinuePropagation

@game_bot.on_message(~filters.bot, group=-20)
async def game_bot_sync_user(client, message):
    """Handler for GameBot to trigger user data sync on every user message."""
    if message.from_user:
        asyncio.create_task(sync_user_data(message))
    raise ContinuePropagation
