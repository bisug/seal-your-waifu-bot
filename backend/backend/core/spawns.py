import asyncio
import datetime
import json
import random
import time
from typing import Any, Dict, Optional
from pyrogram import enums
from pymongo import ReturnDocument

from backend import LOGGER, app
from backend.core.cache import rget, rset
from backend.core.waifu import get_or_load_characters
from backend.database import message_counts_collection
from backend.database import r as _redis
from backend.database import spawns_collection, user_totals_collection

MESSAGE_COUNT_TTL_SECONDS = 86400

# Golden Hour: boosted spawn rates between 20:00 and 22:59 UTC.
GOLDEN_HOUR_START_UTC = 20
GOLDEN_HOUR_END_UTC = 22
# An unclaimed spawn is never replaced while younger than this.
ACTIVE_SPAWN_GRACE_SECONDS = 300


def is_golden_hour(now: Optional[datetime.datetime] = None) -> bool:
    """True during Golden Hour (20:00-22:59 UTC), when spawns are 2x faster."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    return GOLDEN_HOUR_START_UTC <= now.hour <= GOLDEN_HOUR_END_UTC


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
                    elif k == "message_id":
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
                to_cache = {k: (json.dumps(v, default=str) if isinstance(v, dict) else str(v)) for k, v in state.items() if k != "_id"}
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
        # Single round-trip: mark activity + refresh the 10m TTL.
        async with _redis.pipeline(transaction=False) as pipe:
            pipe.zadd(key, {str(user_id): time.time()})
            pipe.expire(key, 600) # 10m TTL
            await pipe.execute()
    except Exception as e: LOGGER.debug(f"Non-critical error (suppressed): {e}")
# Active-user counts change slowly; cache briefly so the per-message spawn
# check doesn't hit Redis on every message.
_active_count_cache: Dict[int, tuple[float, int]] = {}
ACTIVE_COUNT_CACHE_TTL_SECONDS = 30.0


async def get_active_user_count(chat_id: int) -> int:
    """Get count of users active in last 10m (cached for 30s per chat)."""
    if not _redis: return 1 # Default
    now = time.monotonic()
    cached = _active_count_cache.get(chat_id)
    if cached and cached[0] > now:
        return cached[1]
    key = f"spawn:active_users:{chat_id}"
    try:
        # Single round-trip: prune users older than 10 mins, then count.
        async with _redis.pipeline(transaction=False) as pipe:
            pipe.zremrangebyscore(key, "-inf", time.time() - 600)
            pipe.zcard(key)
            _, count = await pipe.execute()
        count = int(count)
        _active_count_cache[chat_id] = (now + ACTIVE_COUNT_CACHE_TTL_SECONDS, count)
        return count
    except Exception as e:
        LOGGER.debug(f"Non-critical error: {e}")
        return 1
async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
    """Register active spawn in cache and DB."""
    key = f"spawn:state:{chat_id}"
    data = {
        "last_character": json.dumps(character, default=str),
        "message_id": str(message_id),
        "first_correct_guess": "None",
        "last_spawn_time": str(time.time())
    }
    if _redis:
        try:
            async with _redis.pipeline(transaction=False) as pipe:
                pipe.hset(key, mapping=data)
                pipe.expire(key, 3600)
                await pipe.execute()
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
                async with _redis.pipeline(transaction=False) as pipe:
                    pipe.hset(key, "first_correct_guess", str(user_id))
                    pipe.hdel(key, "last_character", "message_id")
                    await pipe.execute()
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
# Per-chat spawn frequency changes only via manual DB edits; a short
# in-process cache keeps the per-message spawn check off Redis/Mongo.
_chat_freq_cache: Dict[int, tuple[float, int]] = {}
CHAT_FREQ_CACHE_TTL_SECONDS = 300.0


async def get_chat_frequency(chat_id: int) -> int:
    """Configured spawn frequency for a chat (in-process cache, 5 min TTL)."""
    now = time.monotonic()
    cached = _chat_freq_cache.get(chat_id)
    if cached and cached[0] > now:
        return cached[1]
    key = f"spawn:state:{chat_id}"
    freq = None
    if _redis:
        try:
            freq = await asyncio.wait_for(_redis.hget(key, "_cached_frequency"), timeout=3.0)
            freq = int(freq) if freq else None
        except Exception as e:
            LOGGER.debug(f"Redis frequency cache read failed for {chat_id}: {e}")
    if freq is None:
        doc = await user_totals_collection.find_one({"chat_id": {"$in": [chat_id, str(chat_id)]}}, projection={"message_frequency": 1})
        freq = int(doc["message_frequency"]) if doc and doc.get("message_frequency") else 100
        if _redis:
            try:
                await asyncio.wait_for(_redis.hset(key, "_cached_frequency", str(freq)), timeout=3.0)
            except Exception as e:
                LOGGER.debug(f"Redis frequency cache write failed for {chat_id}: {e}")
    _chat_freq_cache[chat_id] = (now + CHAT_FREQ_CACHE_TTL_SECONDS, freq)
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
    # MGET in chunks: one round-trip per 100 keys instead of one per key.
    for i in range(0, len(keys), 100):
        chunk = keys[i : i + 100]
        try:
            values = await _redis.mget(*chunk)
        except Exception as e:
            LOGGER.error(f"MGET of msg_count keys failed ({len(chunk)} keys): {e}")
            continue
        for key, count in zip(chunk, values):
            if not count:
                continue
            try:
                count_int = int(count)
            except (TypeError, ValueError):
                continue
            ops.append(UpdateOne(
                {"chat_id": key.split(":")[-1]},
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
async def has_recent_unclaimed_spawn(chat_id: int, *, max_age_seconds: float = ACTIVE_SPAWN_GRACE_SECONDS) -> bool:
    """True while an unclaimed spawn is younger than the grace window."""
    state = await get_chat_state(chat_id)
    if not state.get("last_character"):
        return False
    try:
        age = time.time() - float(state.get("last_spawn_time"))
    except (TypeError, ValueError):
        # Character present but timestamp missing/corrupt: treat as fresh.
        return True
    return age < max_age_seconds


async def send_character(chat_id: int, rarity: str, *, force: bool = False):
    """
    Select and send a character of the given rarity to a chat.
    Automatic spawns are skipped while a recent spawn is still unclaimed
    (so it isn't silently replaced); pass force=True to override (/cnow).
    Handles photo sending, caption generation, and royal spawn notifications.
    """
    if not force and await has_recent_unclaimed_spawn(chat_id):
        LOGGER.debug(f"Spawn of {rarity} skipped in {chat_id}: previous spawn still unclaimed")
        return
    chars = await get_or_load_characters(rarity)
    if not chars:
        return
    character = random.choice(chars)
    golden_text = "\n🌟 <b>Golden Hour is Active!</b>" if is_golden_hour() else ""
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
