import asyncio
import datetime
import json
import random
import time
from typing import Any, Dict, Optional
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode
from pymongo import ReturnDocument

from backend import LOGGER, app, config
from backend.core.cache import rget, rset
from backend.core.utils import html_escape
from backend.core.waifu import get_or_load_characters
from backend.database import message_counts_collection
from backend.database import r as _redis
from backend.database import spawns_collection, user_totals_collection

MESSAGE_COUNT_TTL_SECONDS = 86400


def _message_count_from_doc(doc: Optional[Dict[str, Any]]) -> int:
    if not doc:
        return 0
    try:
        stored_count = int(doc.get("count") or 0)
    except (TypeError, ValueError):
        stored_count = 0
    users = doc.get("users") or {}
    user_total = 0
    if isinstance(users, dict):
        for value in users.values():
            try:
                user_total += int(value)
            except (TypeError, ValueError):
                continue
    return max(stored_count, user_total)


async def _load_message_count_from_mongo(chat_id: int) -> int:
    chat_id_str = str(chat_id)
    doc = await message_counts_collection.find_one({"chat_id": chat_id_str})
    count = _message_count_from_doc(doc)
    if doc and doc.get("count") != count:
        await message_counts_collection.update_one(
            {"chat_id": chat_id_str},
            {"$max": {"count": count}},
        )
    return count


async def _persist_message_increment(chat_id: int, user_id: int, count: int) -> None:
    await message_counts_collection.update_one(
        {"chat_id": str(chat_id)},
        {
            "$max": {"count": int(count)},
            "$inc": {f"users.{user_id}": 1},
        },
        upsert=True,
    )


# In-memory buffer of message increments awaiting MongoDB persistence.
# Flushed by flush_cache_to_db() every minute and at shutdown, turning one
# Mongo write per message into one bulk_write per flush interval.
_pending_increments: Dict[int, Dict[str, Any]] = {}


def _record_pending_increment(chat_id: int, user_id: int) -> None:
    entry = _pending_increments.setdefault(chat_id, {"count": 0, "users": {}})
    entry["count"] += 1
    users = entry["users"]
    users[user_id] = users.get(user_id, 0) + 1


async def flush_pending_message_increments() -> int:
    """Drain the pending increment buffer into MongoDB with a single bulk write."""
    if not _pending_increments:
        return 0
    pending = dict(_pending_increments)
    _pending_increments.clear()

    from pymongo import UpdateOne

    ops = []
    for chat_id, entry in pending.items():
        inc: Dict[str, int] = {"count": entry["count"]}
        for uid, n in entry["users"].items():
            inc[f"users.{uid}"] = n
        ops.append(
            UpdateOne(
                {"chat_id": str(chat_id)},
                {"$inc": inc},
                upsert=True,
            )
        )
    try:
        await message_counts_collection.bulk_write(ops, ordered=False)
    except Exception as e:
        # Re-queue so the next flush retries instead of losing counts.
        for chat_id, entry in pending.items():
            target = _pending_increments.setdefault(chat_id, {"count": 0, "users": {}})
            target["count"] += entry["count"]
            for uid, n in entry["users"].items():
                target["users"][uid] = target["users"].get(uid, 0) + n
        LOGGER.error(f"Bulk flush of message increments failed ({len(ops)} chats): {e}")
        return 0
    return len(ops)


async def _increment_message_count_mongo(chat_id: int, user_id: int) -> int:
    await _load_message_count_from_mongo(chat_id)
    updated = await message_counts_collection.find_one_and_update(
        {"chat_id": str(chat_id)},
        {
            "$inc": {"count": 1, f"users.{user_id}": 1},
            "$setOnInsert": {"chat_id": str(chat_id)},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    count = _message_count_from_doc(updated)
    await rset(f"msg_count:{chat_id}", str(count), ttl=MESSAGE_COUNT_TTL_SECONDS)
    return count


async def get_chat_state(chat_id: int) -> Dict[str, Any]:
    """Retrieve chat state from Redis with MongoDB fallback."""
    key = f"spawn:state:{chat_id}"
    if _redis:
        try:
            state = await _redis.hgetall(key)
            if state:
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
                        except Exception: parsed_state[k] = time.time() # Guard against malformed time
                    else:
                        parsed_state[k] = v
                return parsed_state
        except Exception as e:
            LOGGER.warning(f"Redis get_chat_state error: {e}")
    # Fallback to MongoDB
    state = await spawns_collection.find_one({"chat_id": chat_id})
    if _redis:
        try:
            if state:
                to_cache = {k: (json.dumps(v) if isinstance(v, dict) else str(v)) for k, v in state.items() if k != "_id"}
                if to_cache:
                    await _redis.hset(key, mapping=to_cache)
            else:
                await _redis.hset(key, mapping={"_no_state": "1"})
            await _redis.expire(key, 3600)
        except Exception as e: LOGGER.debug(f"Persistence error: {e}")
    return state or {}
async def track_user_activity(chat_id: int, user_id: int):
    """Track active users using a Redis Sorted Set (ZSET)."""
    if not _redis: return
    key = f"spawn:active_users:{chat_id}"
    try:
        await _redis.zadd(key, {str(user_id): time.time()})
        await _redis.expire(key, 600) # 10m TTL
    except Exception as e: LOGGER.debug(f"Non-critical error (suppressed): {e}")
async def get_active_user_count(chat_id: int) -> int:
    """Get count of users active in last 10m."""
    if not _redis: return 1 # Default
    key = f"spawn:active_users:{chat_id}"
    try:
        now = time.time()
        # Remove users older than 10 mins
        await _redis.zremrangebyscore(key, "-inf", now - 600)
        return await _redis.zcard(key)
    except Exception as e:
        LOGGER.debug(f"Non-critical error: {e}")
        return 1
async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
    """Register active spawn in cache and DB."""
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
    """Clear active spawn if guess is correct."""
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
            except Exception as e: LOGGER.debug(f"Persistence error: {e}")
        return True
    return False
async def get_message_count(chat_id: int) -> int:
    key = f"msg_count:{chat_id}"
    val = await rget(key)
    if val is not None: return int(val)
    # Fallback/Init from Mongo
    count = await _load_message_count_from_mongo(chat_id)
    await rset(key, str(count), ttl=MESSAGE_COUNT_TTL_SECONDS) # 24h TTL for memory safety
    return count
async def increment_message_count(chat_id: int, user_id: int) -> int:
    """Increments the message count for a chat and a specific user."""
    key = f"msg_count:{chat_id}"
    if _redis:
        try:
            # Single round-trip: seed-if-missing + increment + TTL refresh.
            async with _redis.pipeline(transaction=False) as pipe:
                pipe.set(key, 0, ex=MESSAGE_COUNT_TTL_SECONDS, nx=True)
                pipe.incr(key)
                pipe.expire(key, MESSAGE_COUNT_TTL_SECONDS)
                seeded, count, _ = await pipe.execute()
            count = int(count)
            if seeded:
                # We won the seed race: layer the stored Mongo total on top of
                # the fresh counter. INCRBY keeps concurrent increments intact.
                initial_count = await _load_message_count_from_mongo(chat_id)
                if initial_count > 0:
                    count = int(await _redis.incrby(key, initial_count))
                    await _redis.expire(key, MESSAGE_COUNT_TTL_SECONDS)
                LOGGER.info(f"Initialized Redis counter for {chat_id} at {count}")
        except Exception as e:
            LOGGER.error(f"Redis increment failed for {chat_id}: {e}")
        else:
            _record_pending_increment(chat_id, user_id)
            return count
    # Fallback to atomic DB-backed tracking.
    return await _increment_message_count_mongo(chat_id, user_id)
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
        try:
            freq = await asyncio.wait_for(_redis.hget(key, "_cached_frequency"), timeout=3.0)
            if freq: return int(freq)
        except Exception as e:
            LOGGER.debug(f"Redis frequency cache read failed for {chat_id}: {e}")
    doc = await user_totals_collection.find_one({"chat_id": {"$in": [chat_id, str(chat_id)]}}, projection={"message_frequency": 1})
    freq = int(doc["message_frequency"]) if doc and doc.get("message_frequency") else 100
    if _redis:
        try:
            await asyncio.wait_for(_redis.hset(key, "_cached_frequency", str(freq)), timeout=3.0)
        except Exception as e:
            LOGGER.debug(f"Redis frequency cache write failed for {chat_id}: {e}")
    return freq
async def flush_message_counts_to_db() -> int:
    """Sync cached Redis message totals to MongoDB once (batched bulk writes)."""
    if not _redis: return 0
    from pymongo import UpdateOne
    from backend.core.cache import _scan_keys
    synced = 0
    ops = []

    async def write_batch() -> None:
        nonlocal ops
        if not ops:
            return
        batch, ops = ops, []
        try:
            await message_counts_collection.bulk_write(batch, ordered=False)
        except Exception as e:
            LOGGER.error(f"Bulk flush of msg_count totals failed ({len(batch)} chats): {e}")

    keys = await _scan_keys("msg_count:*")
    for key in keys:
        chat_id_str = key.split(":")[-1]
        count = await _redis.get(key)
        if not count:
            continue
        try:
            count_int = int(count)
        except (TypeError, ValueError):
            continue
        ops.append(UpdateOne(
            {"chat_id": chat_id_str},
            {"$max": {"count": count_int}},
            upsert=True,
        ))
        synced += 1
        if len(ops) >= 500:
            await write_batch()
    await write_batch()
    return synced


async def flush_cache_to_db():
    """Sync message counts from Redis to MongoDB periodically."""
    if not _redis: return
    while True:
        await asyncio.sleep(60)
        try:
            await flush_pending_message_increments()
            await flush_message_counts_to_db()
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
        # Use the safe wrapper to handle FloodWait automatically with exponential backoff
        msg = await app.send_media_safe(
            chat_id,
            media_url=character['img_url'],
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            has_spoiler=True
        )
        if not msg:
            LOGGER.warning(f"send_character: failed to send spawn to {chat_id} (FloodWait or peer error)")
            return
        # Register the spawn as active in the persistent state
        await set_active_spawn(chat_id, character, msg.id)
    except Exception as e:
        LOGGER.error(f"Error sending character: {e}")
