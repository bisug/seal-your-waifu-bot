import asyncio
import json
import time
from typing import Any, Dict, Optional

from pymongo import ReturnDocument
from pyrogram import enums

from backend.client import app
from backend.core.cache import rget, rset
from backend.core.logging import get_logger
from backend.core.tasks import run_background_task
from backend.core.waifu import _pick_excluding, get_or_load_characters
from backend.database import message_counts_collection, spawns_collection
from backend.database import r as _redis

LOGGER = get_logger(__name__)

MESSAGE_COUNT_TTL_SECONDS = 86400

# Unclaimed spawns are never replaced while younger than this.
ACTIVE_SPAWN_GRACE_SECONDS = 300


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


# Pending increments, bulk-flushed to Mongo every minute.
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
        # Re-queue for the next flush instead of losing counts.
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


def _parse_redis_state(state: Dict[bytes, Any]) -> Dict[str, Any]:
    """Convert a raw Redis hash into typed chat-state values."""
    parsed_state = {}
    for k, v in state.items():
        if v == "None":
            parsed_state[k] = None
        elif v == "True":
            parsed_state[k] = True
        elif v == "False":
            parsed_state[k] = False
        elif k == "last_character":
            try:
                parsed_state[k] = json.loads(v)
            except (ValueError, TypeError):
                parsed_state[k] = v
        elif k == "message_id":
            try:
                parsed_state[k] = int(v)
            except (ValueError, TypeError):
                parsed_state[k] = v
        elif k == "last_spawn_time":
            try:
                parsed_state[k] = float(v)
            except (ValueError, TypeError):
                parsed_state[k] = time.time()  # Guard against malformed time
        else:
            parsed_state[k] = v
    return parsed_state

async def _write_state_to_redis(key: str, state: Dict[str, Any]) -> None:
    """Cache a Mongo chat-state doc (or its absence) in Redis with a 1h TTL."""
    if not _redis:
        return
    try:
        if state:
            to_cache = {
                k: (json.dumps(v, default=str) if isinstance(v, dict) else str(v))
                for k, v in state.items()
                if k != "_id"
            }
            if to_cache:
                await _redis.hset(key, mapping=to_cache)
        else:
            await _redis.hset(key, mapping={"_no_state": "1"})
        await _redis.expire(key, 3600)
    except Exception as e:
        LOGGER.debug(f"Persistence error: {e}")


async def get_chat_state(chat_id: int) -> Dict[str, Any]:
    """Retrieve chat state from Redis with MongoDB fallback."""
    key = f"spawn:state:{chat_id}"
    if _redis:
        try:
            state = await _redis.hgetall(key)
            if state:
                return _parse_redis_state(state)
        except Exception as e:
            LOGGER.warning(f"Redis get_chat_state error: {e}")
    state = await spawns_collection.find_one({"chat_id": chat_id})
    await _write_state_to_redis(key, state)
    return state or {}
async def track_user_activity(chat_id: int, user_id: int):
    """Track active users using a Redis Sorted Set (ZSET)."""
    if not _redis: return
    key = f"spawn:active_users:{chat_id}"
    try:
        async with _redis.pipeline(transaction=False) as pipe:
            pipe.zadd(key, {str(user_id): time.time()})
            pipe.expire(key, 600)
            await pipe.execute()
    except Exception as e: LOGGER.debug(f"Non-critical error (suppressed): {e}")
# 30s cache so the per-message spawn check skips Redis.
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
    mongo_data = {
        "last_character": character,
        "message_id": message_id,
        "first_correct_guess": None,
        "last_spawn_time": time.time()
    }
    # Mongo is only the fallback store (/seal reads Redis first); deferring
    # this write takes the Mongo round trip off the spawn-critical path.
    run_background_task(
        spawns_collection.update_one({"chat_id": chat_id}, {"$set": mongo_data}, upsert=True)
    )
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
    count = await _load_message_count_from_mongo(chat_id)
    await rset(key, str(count), ttl=MESSAGE_COUNT_TTL_SECONDS) # 24h TTL for memory safety
    return count
async def increment_message_count(chat_id: int, user_id: int) -> int:
    """Increments the message count for a chat and a specific user."""
    key = f"msg_count:{chat_id}"
    if _redis:
        try:
            async with _redis.pipeline(transaction=False) as pipe:
                pipe.set(key, 0, ex=MESSAGE_COUNT_TTL_SECONDS, nx=True)
                pipe.incr(key)
                pipe.expire(key, MESSAGE_COUNT_TTL_SECONDS)
                seeded, count, _ = await pipe.execute()
            count = int(count)
            if seeded:
                # Won the seed race: layer the stored Mongo total on top.
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
    return await _increment_message_count_mongo(chat_id, user_id)
# 5 min in-process cache; frequency only changes via manual DB edits.
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
        # No per-chat frequency is configured anywhere; the default keeps
        # spawn pacing uniform until an admin knob exists.
        freq = 100
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


# How many recent spawns per chat to exclude from the next pick. Small enough
# to stay cheap, large enough that a chat never sees the same face twice in a
# row (unless the rarity pool is tiny).
RECENT_SPAWN_HISTORY = 30
RECENT_SPAWN_TTL_SECONDS = 86400


async def _get_recent_spawn_ids(chat_id: int) -> list:
    """Character ids spawned in this chat recently (Redis list, newest first)."""
    if not _redis:
        return []
    try:
        ids = await _redis.lrange(f"spawn:recent:{chat_id}", 0, -1)
        return [i.decode() if isinstance(i, bytes) else str(i) for i in ids]
    except Exception as e:
        LOGGER.debug(f"Recent-spawn read failed for {chat_id}: {e}")
        return []


async def _record_recent_spawn(chat_id: int, char_id: str) -> None:
    """Push a spawned character id onto the chat's recent list (capped)."""
    if not _redis:
        return
    try:
        key = f"spawn:recent:{chat_id}"
        async with _redis.pipeline(transaction=False) as pipe:
            pipe.lpush(key, char_id)
            pipe.ltrim(key, 0, RECENT_SPAWN_HISTORY - 1)
            pipe.expire(key, RECENT_SPAWN_TTL_SECONDS)
            await pipe.execute()
    except Exception as e:
        LOGGER.debug(f"Recent-spawn write failed for {chat_id}: {e}")


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
    # Overlap the two independent lookups (recent-spawn exclusion list and
    # the rarity pool) with the guard check above, so the pre-send latency
    # is one round trip instead of three sequential ones.
    recent_task = asyncio.create_task(_get_recent_spawn_ids(chat_id))
    chars_task = asyncio.create_task(get_or_load_characters(rarity))
    try:
        chars = await chars_task
        if not chars:
            return
        character = _pick_excluding(chars, await recent_task)
        caption = (
            "🪽 <b>A new character appeared!</b>\n"
            "🦋 Use /seal name to collect them!\n"
            "👑 Rarity is secret until caught!"
        )
        try:
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
            await set_active_spawn(chat_id, character, msg.id)
            # Variety bookkeeping is not spawn-critical — keep it off the path.
            run_background_task(_record_recent_spawn(chat_id, str(character.get("id"))))
        except Exception as e:
            LOGGER.error(f"Error sending character: {e}")
    finally:
        for task in (recent_task, chars_task):
            if not task.done():
                task.cancel()


# --- Pokémon spawns (guess-the-Pokémon minigame) ---

# How often a Pokémon spawn fires instead of a character spawn (1 in N).
POKEMON_SPAWN_EVERY = 8
POKEMON_SPAWN_STATE_TTL = 3600  # Redis state expiry, matches character spawns
# Unguessed Pokémon spawns stop blocking new ones after this window (Mongo
# fallback docs carry an expires_at_dt TTL index; reads filter on it too).
POKEMON_SPAWN_MAX_AGE_SECONDS = 1800
POKEMON_GUESS_REWARD = 150      # coins for a correct guess
POKEMON_GUESS_XP = 15           # user XP for a correct guess
POKEMON_GUESS_MON_XP = 25      # active-partner XP for a correct guess

# In-process fallback for the Pokémon spawn slot counter (Redis-less mode).
_pokemon_slot_counter: Dict[int, int] = {}


async def _next_pokemon_spawn_slot(chat_id: int) -> bool:
    """True when this spawn slot is the Pokémon one (stable 1-in-N counter).

    Uses its own Redis counter so fluctuating character-spawn frequency
    (activity-based target_freq) can't make the Pokémon slot un-hittable.
    Falls back to a deterministic in-process counter when Redis is down.
    """
    n = POKEMON_SPAWN_EVERY
    if not _redis:
        _pokemon_slot_counter[chat_id] = (_pokemon_slot_counter.get(chat_id, 0) + 1) % n
        return _pokemon_slot_counter[chat_id] == 0
    try:
        key = f"pokespawn:slot:{chat_id}"
        async with _redis.pipeline(transaction=False) as pipe:
            pipe.incr(key)
            pipe.expire(key, 86400)
            slot, _ = await pipe.execute()
        return int(slot) % n == 0
    except Exception as e:
        LOGGER.debug(f"Pokémon slot counter failed for {chat_id}: {e}")
        return False


async def send_pokemon_spawn(chat_id: int) -> None:
    """Send a random catalog Pokémon silhouette for the guess minigame.

    The artwork is sent as a spoiler so it stays hidden until guessed —
    the name is never shown. State mirrors character spawns: Redis hash
    first, Mongo fallback, atomic claim on correct guess.
    """
    from backend.database import pokemon_catalog_collection

    pipeline = [{"$match": {"enabled": True}}, {"$sample": {"size": 1}}]
    cursor = pokemon_catalog_collection.aggregate(pipeline)
    docs = await cursor.to_list(length=1)
    if not docs:
        return
    mon = docs[0]
    caption = (
        "🌀 <b>A wild Pokémon appeared!</b>\n"
        "❓ Guess its name to win a reward!\n"
        "💬 Type the name in chat (no command needed)."
    )
    try:
        msg = await app.send_media_safe(
            chat_id,
            media_url=mon["img"],
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            has_spoiler=True,
        )
        if not msg:
            LOGGER.warning(f"send_pokemon_spawn: failed to send to {chat_id}")
            return
        await set_active_pokemon_spawn(chat_id, mon, msg.id)
    except Exception as e:
        LOGGER.error(f"Error sending Pokémon spawn: {e}")


async def set_active_pokemon_spawn(chat_id: int, mon: Dict[str, Any], message_id: int) -> None:
    """Register the active Pokémon spawn (Redis hash + Mongo fallback).

    Uses a dedicated `_id` (`pokespawn:{chat_id}`) so the doc can never
    collide with the character-spawn doc for the same chat.
    """
    key = f"pokespawn:state:{chat_id}"
    data = {
        "dex": str(mon["dex"]),
        "name": mon["name"],
        "message_id": str(message_id),
        "last_spawn_time": str(time.time()),
    }
    if _redis:
        try:
            async with _redis.pipeline(transaction=False) as pipe:
                pipe.hset(key, mapping=data)
                pipe.expire(key, POKEMON_SPAWN_STATE_TTL)
                await pipe.execute()
        except Exception as e:
            LOGGER.debug(f"Redis operation bypassed: {e}")
    run_background_task(
        spawns_collection.update_one(
            {"_id": f"pokespawn:{chat_id}"},
            {"$set": {"kind": "pokemon", "pokemon": mon, "message_id": message_id,
                      "last_spawn_time": time.time(),
                      "expires_at_dt": time.time() + POKEMON_SPAWN_MAX_AGE_SECONDS}},
            upsert=True,
        )
    )


async def get_active_pokemon_spawn(chat_id: int) -> Optional[Dict[str, Any]]:
    """Active Pokémon spawn for this chat: {dex, name, message_id} or None.

    Stale spawns (older than POKEMON_SPAWN_MAX_AGE_SECONDS) read as gone,
    so an unguessed Pokémon never permanently blocks the next one.
    """
    key = f"pokespawn:state:{chat_id}"
    if _redis:
        try:
            raw = await _redis.hgetall(key)
            state = {
                (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
                for k, v in (raw or {}).items()
            }
            if state.get("dex"):
                return {
                    "dex": int(state["dex"]),
                    "name": state["name"],
                    "message_id": int(state["message_id"]),
                }
        except Exception as e:
            LOGGER.debug(f"Redis read bypassed: {e}")
    doc = await spawns_collection.find_one({
        "_id": f"pokespawn:{chat_id}",
        "pokemon": {"$ne": None},
        "last_spawn_time": {"$gt": time.time() - POKEMON_SPAWN_MAX_AGE_SECONDS},
    })
    if not doc or not doc.get("pokemon"):
        return None
    return {
        "dex": doc["pokemon"]["dex"],
        "name": doc["pokemon"]["name"],
        "message_id": doc.get("message_id"),
    }


async def clear_active_pokemon_spawn(chat_id: int, user_id: int) -> bool:
    """Atomically claim the Pokémon spawn for this user. False if already won."""
    result = await spawns_collection.update_one(
        {"_id": f"pokespawn:{chat_id}", "pokemon": {"$ne": None}},
        {"$set": {"winner_id": user_id}, "$unset": {"pokemon": "", "message_id": ""}},
    )
    if result.modified_count > 0:
        if _redis:
            try:
                key = f"pokespawn:state:{chat_id}"
                async with _redis.pipeline(transaction=False) as pipe:
                    pipe.delete(key)
                    await pipe.execute()
            except Exception as e:
                LOGGER.debug(f"Redis clear bypassed: {e}")
        return True
    return False
