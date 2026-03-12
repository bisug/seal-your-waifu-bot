import time
import random
import datetime
import asyncio
from typing import Optional, Dict, Any
from pyrogram import enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber.database import spawns_collection, message_counts_collection, user_totals_collection
from Grabber import app, LOGGER, config
from Grabber.core.waifu import get_or_load_characters

# --- IN-MEMORY CACHE FOR PERFORMANCE ---
MESSAGE_COUNTS_CACHE: Dict[int, int] = {}
CHAT_STATE_CACHE: Dict[int, Dict[str, Any]] = {}

async def load_chat_state_if_needed(chat_id: int):
    """
    Ensure the chat state is loaded into the in-memory cache.
    """
    if chat_id not in CHAT_STATE_CACHE:
        state = await spawns_collection.find_one({"chat_id": chat_id})
        CHAT_STATE_CACHE[chat_id] = state or {}

async def load_message_count_if_needed(chat_id: int):
    """
    Ensure the chat message count is loaded into the in-memory cache.
    """
    if chat_id not in MESSAGE_COUNTS_CACHE:
        doc = await message_counts_collection.find_one({"chat_id": str(chat_id)})
        MESSAGE_COUNTS_CACHE[chat_id] = doc["count"] if doc else 0


async def track_user_activity(chat_id: int, user_id: int):
    """
    Update the last seen timestamp for a user in a specific chat.
    Used to track chat activity levels.
    """
    # Track purely in memory
    await load_chat_state_if_needed(chat_id)
    current_time = time.time()
    if "active_users" not in CHAT_STATE_CACHE[chat_id]:
        CHAT_STATE_CACHE[chat_id]["active_users"] = {}
    CHAT_STATE_CACHE[chat_id]["active_users"][str(user_id)] = current_time

async def get_active_user_count(chat_id: int) -> int:
    """
    Calculate the number of users seen in the last 10 minutes for a chat.
    """
    await load_chat_state_if_needed(chat_id)
    active_dict = CHAT_STATE_CACHE[chat_id].get("active_users", {})
    current_time = time.time()
    active_count = sum(1 for ts in active_dict.values() if ts > current_time - 600)
    return active_count

async def get_chat_state(chat_id: int) -> Dict[str, Any]:
    await load_chat_state_if_needed(chat_id)
    return CHAT_STATE_CACHE[chat_id]

async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
    """
    Register a new character spawn as active in a chat.
    Persists to DB immediately for safety.
    """
    await load_chat_state_if_needed(chat_id)
    # Update cache
    CHAT_STATE_CACHE[chat_id].update({
        "last_character": character,
        "message_id": message_id,
        "first_correct_guess": None,
        "last_spawn_time": time.time()
    })
    # We still write spawn explicitly directly to DB to prevent dataloss of an active spawn if bot crashes
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {"$set": CHAT_STATE_CACHE[chat_id]},
        upsert=True
    )

async def clear_active_spawn(chat_id: int, user_id: int) -> bool:
    """
    Atomically clear the active spawn and set the first correct guesser.
    """
    await load_chat_state_if_needed(chat_id)

    result = await spawns_collection.update_one(
        {
            "chat_id": chat_id,
            "last_character": {"$ne": None},
            "first_correct_guess": None
        },
        {
            "$set": {"first_correct_guess": user_id},
            "$unset": {"last_character": "", "message_id": ""}
        }
    )
    if result.modified_count > 0:
        # Update cache to reflect db change
        CHAT_STATE_CACHE[chat_id]["first_correct_guess"] = user_id
        CHAT_STATE_CACHE[chat_id].pop("last_character", None)
        CHAT_STATE_CACHE[chat_id].pop("message_id", None)
        return True
    return False

async def get_message_count(chat_id: int) -> int:
    await load_message_count_if_needed(chat_id)
    return MESSAGE_COUNTS_CACHE[chat_id]

async def increment_message_count(chat_id: int) -> int:
    await load_message_count_if_needed(chat_id)
    MESSAGE_COUNTS_CACHE[chat_id] += 1
    return MESSAGE_COUNTS_CACHE[chat_id]

async def get_spawn_order(chat_id: int) -> int:
    await load_chat_state_if_needed(chat_id)
    return CHAT_STATE_CACHE[chat_id].get("spawn_order", 0)

async def increment_spawn_order(chat_id: int):
    await load_chat_state_if_needed(chat_id)
    CHAT_STATE_CACHE[chat_id]["spawn_order"] = CHAT_STATE_CACHE[chat_id].get("spawn_order", 0) + 1

async def get_chat_frequency(chat_id: int) -> int:
    """
    Retrieve the configured message frequency for spawns in a chat.
    Cached in CHAT_STATE_CACHE after the first DB lookup — frequency rarely
    changes, so this eliminates repeated DB queries on every group message.
    Defaults to 100 if not set.
    """
    await load_chat_state_if_needed(chat_id)
    cached = CHAT_STATE_CACHE[chat_id].get("_cached_frequency")
    if cached is not None:
        return cached
    doc = await user_totals_collection.find_one(
        {"chat_id": str(chat_id)},
        projection={"message_frequency": 1}
    )
    freq = int(doc["message_frequency"]) if doc and doc.get("message_frequency") else 100
    CHAT_STATE_CACHE[chat_id]["_cached_frequency"] = freq
    return freq

async def flush_cache_to_db():
    """
    Periodic background task that flushes in-memory counters and states
    to the MongoDB database to ensure persistence.
    """
    while True:
        await asyncio.sleep(60)
        try:
            # 1. Flush message counts
            for chat_id, count in list(MESSAGE_COUNTS_CACHE.items()):
                await message_counts_collection.update_one(
                    {"chat_id": str(chat_id)},
                    {"$set": {"count": count}},
                    upsert=True
                )
            # 2. Flush chat states
            for chat_id, state in list(CHAT_STATE_CACHE.items()):
                # Clean up old active users to keep state small
                current_time = time.time()
                active_users = state.get("active_users", {})
                cleaned_users = {uid: ts for uid, ts in active_users.items() if ts > current_time - 600}
                state["active_users"] = cleaned_users

                await spawns_collection.update_one(
                    {"chat_id": chat_id},
                    {"$set": state},
                    upsert=True
                )
        except Exception as e:
            LOGGER.error(f"Error flushing cache: {e}")


async def send_character(chat_id: int, rarity: str):
    """
    Select and send a character of the given rarity to a chat.
    Handles photo sending, caption generation, and royal spawn notifications.
    """
    chars = await get_or_load_characters(rarity)
    if not chars:
        return

    character = random.choice(chars)


    now = datetime.datetime.now(datetime.timezone.utc)
    golden_text = ""
    if 20 <= now.hour <= 22:
        golden_text = "\n🌟 <b>Golden Hour is Active!</b>"

    caption = (
        "🪽 <b>A new character appeared!</b>\n"
        "🦋 Use /seal name to collect them!\n"
        "👑 Rarity is secret until caught!"
        f"{golden_text}"
    )

    try:
        msg = await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode=ParseMode.HTML
        )
        await set_active_spawn(chat_id, character, msg.id)

    except Exception as e:
        LOGGER.error(f"Error sending character: {e}")
