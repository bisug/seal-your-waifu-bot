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
import time
import random
import datetime
import asyncio
import json
from typing import Optional, Dict, Any
from pyrogram import enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber.database import spawns_collection, message_counts_collection, user_totals_collection, r as _redis
from Grabber import app, LOGGER, config
from Grabber.core.waifu import get_or_load_characters

# --- REDIS KEYS ---
# msg_count:{chat_id} -> str (int)
# spawn:state:{chat_id} -> hash
# spawn:active_users:{chat_id} -> zset (uid: timestamp)

async def _rget(key: str) -> Optional[str]:
    if not _redis: return None
    try: return await _redis.get(key)
    except Exception: return None

async def _rset(key: str, val: str, ex: int = None):
    if not _redis: return
    try: await _redis.set(key, val, ex=ex)
    except Exception: pass

async def get_chat_state(chat_id: int) -> Dict[str, Any]:
    """Retrieve chat state from Redis hash, falling back to MongoDB."""
    key = f"spawn:state:{chat_id}"
    if _redis:
        try:
            state = await _redis.hgetall(key)
            if state:
                # Redis hgetall returns a dict of strings. We need to parse them.
                parsed_state = {}
                for k, v in state.items():
                    # Handle basic types
                    if v == "None": parsed_state[k] = None
                    elif v == "True": parsed_state[k] = True
                    elif v == "False": parsed_state[k] = False
                    elif k == "last_character":
                        try: parsed_state[k] = json.loads(v)
                        except: parsed_state[k] = v
                    elif k in ["message_id", "spawn_order"]:
                        try: parsed_state[k] = int(v)
                        except: parsed_state[k] = v
                    elif k == "last_spawn_time":
                        try: parsed_state[k] = float(v)
                        except: parsed_state[k] = v
                    else:
                        parsed_state[k] = v
                return parsed_state
        except Exception as e:
            LOGGER.warning(f"Redis get_chat_state error: {e}")
    
    # Fallback to MongoDB
    state = await spawns_collection.find_one({"chat_id": chat_id})
    if state and _redis:
        # Repopulate Redis
        try:
            to_cache = {k: (json.dumps(v) if isinstance(v, dict) else str(v)) for k, v in state.items() if k != "_id"}
            if to_cache:
                await _redis.hset(key, mapping=to_cache)
                await _redis.expire(key, 3600) # 1h TTL
        except: pass
    return state or {}

async def track_user_activity(chat_id: int, user_id: int):
    """Track active users using a Redis Sorted Set (ZSET)."""
    if not _redis: return
    key = f"spawn:active_users:{chat_id}"
    try:
        await _redis.zadd(key, {str(user_id): time.time()})
        await _redis.expire(key, 600) # 10m TTL
    except Exception: pass

async def get_active_user_count(chat_id: int) -> int:
    """Get count of users active in the last 10 minutes."""
    if not _redis: return 1 # Default
    key = f"spawn:active_users:{chat_id}"
    try:
        now = time.time()
        # Remove users older than 10 mins
        await _redis.zremrangebyscore(key, "-inf", now - 600)
        return await _redis.zcard(key)
    except Exception: return 1

async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
    """Register active spawn in Redis and MongoDB."""
    key = f"spawn:state:{chat_id}"
    data = {
        "last_character": json.dumps(character),
        "message_id": str(message_id),
        "first_correct_guess": "None",
        "last_spawn_time": str(time.time())
    }
    if _redis:
        try:
            await _redis.hset(key, mapping=data)
            await _redis.expire(key, 3600)
        except Exception as e: LOGGER.debug(f"Redis operation bypassed: {e}")
    
    # Still write to MongoDB for absolute safety (active spawns are high-value)
    mongo_data = {
        "last_character": character,
        "message_id": message_id,
        "first_correct_guess": None,
        "last_spawn_time": time.time()
    }
    await spawns_collection.update_one({"chat_id": chat_id}, {"$set": mongo_data}, upsert=True)

async def clear_active_spawn(chat_id: int, user_id: int) -> bool:
    """Clear active spawn from Redis and MongoDB if guess is correct."""
    # Attempt atomic update in MongoDB first (as it's the source of truth for claims)
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
        if _redis:
            try:
                key = f"spawn:state:{chat_id}"
                await _redis.hset(key, "first_correct_guess", str(user_id))
                await _redis.hdel(key, "last_character", "message_id")
            except Exception as e: LOGGER.debug(f"Redis operation bypassed: {e}")
        return True
    return False

async def get_message_count(chat_id: int) -> int:
    key = f"msg_count:{chat_id}"
    val = await _rget(key)
    if val is not None: return int(val)
    
    # Fallback/Init from Mongo
    doc = await message_counts_collection.find_one({"chat_id": str(chat_id)})
    count = doc["count"] if doc else 0
    await _rset(key, str(count), ex=86400) # 24h TTL for memory safety
    return count

async def increment_message_count(chat_id: int) -> int:
    key = f"msg_count:{chat_id}"
    if _redis:
        try:
            count = await _redis.incr(key)
            await _redis.expire(key, 86400) # Ensure TTL on every increment
            return count
        except Exception as e: LOGGER.debug(f"Redis operation bypassed: {e}")
    
    # Fallback to local
    count = await get_message_count(chat_id) + 1
    await _rset(key, str(count), ex=86400)
    return count

async def get_spawn_order(chat_id: int) -> int:
    state = await get_chat_state(chat_id)
    return int(state.get("spawn_order", 0))

async def increment_spawn_order(chat_id: int):
    key = f"spawn:state:{chat_id}"
    if _redis:
        try:
            await _redis.hincrby(key, "spawn_order", 1)
            return
        except Exception as e: LOGGER.debug(f"Redis operation bypassed: {e}")
    
    # Fallback
    state = await get_chat_state(chat_id)
    new_order = int(state.get("spawn_order", 0)) + 1
    await spawns_collection.update_one({"chat_id": chat_id}, {"$set": {"spawn_order": new_order}}, upsert=True)

async def get_chat_frequency(chat_id: int) -> int:
    key = f"spawn:state:{chat_id}"
    if _redis:
        freq = await _redis.hget(key, "_cached_frequency")
        if freq: return int(freq)

    doc = await user_totals_collection.find_one({"chat_id": str(chat_id)}, projection={"message_frequency": 1})
    freq = int(doc["message_frequency"]) if doc and doc.get("message_frequency") else 100
    
    if _redis:
        try: await _redis.hset(key, "_cached_frequency", str(freq))
        except: pass
    return freq

async def flush_cache_to_db():
    """
    Periodic task to sync message counts from Redis back to MongoDB for long-term storage and recovery.
    State (active spawns) is already write-through.
    """
    if not _redis: return
    while True:
        await asyncio.sleep(60)
        try:
            # Sync message counts
            keys = await _redis.keys("msg_count:*")
            for key in keys:
                chat_id = key.split(":")[-1]
                count = await _redis.get(key)
                if count:
                    await message_counts_collection.update_one(
                        {"chat_id": str(chat_id)},
                        {"$set": {"count": int(count)}},
                        upsert=True
                    )
        except Exception as e:
            LOGGER.error(f"Error flushing count cache to DB: {e}")


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
