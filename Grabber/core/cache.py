"""
Centralized Redis cache layer. All methods are failsafe (falls back to MongoDB).
Key prefixes: user, balance, cooldown, lb, session, gamebot_groups.
"""
import asyncio
import json
import time
from typing import Any, List, Optional
from Grabber import LOGGER
from Grabber.core.utils import get_now_utc
from Grabber.database import r as _redis
r = _redis
# TTL settings (seconds)
TTL_USER        = 60
TTL_LEADERBOARD = 300
TTL_SESSION     = 1800
TTL_DAILY       = 86400
TTL_WEEKLY      = 604800
TTL_GAMEBOT     = 300
MEM_LIMIT_BYTES = 25 * 1024 * 1024 
async def rget(key: str) -> Optional[str]:
    """Get a string value from Redis. Returns None on miss or error."""
    if not _redis:
        return None
    try:
        return await asyncio.wait_for(_redis.get(key), timeout=3.0)
    except asyncio.TimeoutError:
        LOGGER.warning(f"Redis GET timeout [{key}]")
        return None
    except Exception as e:
        LOGGER.warning(f"Redis GET error [{key}]: {e}")
        return None
async def rset(key: str, value: str, ttl: int):
    """Set a string value in Redis with a TTL. Silently ignores errors."""
    if not _redis:
        return
    try:
        # Check memory before setting large key or frequently
        await check_memory_and_purge()
        await asyncio.wait_for(_redis.setex(key, ttl, value), timeout=3.0)
    except asyncio.TimeoutError:
        LOGGER.warning(f"Redis SET timeout [{key}]")
    except Exception as e:
        LOGGER.warning(f"Redis SET error [{key}]: {e}")
async def _scan_keys(pattern: str) -> list:
    """Non-blocking async SCAN replacement for KEYS. Safe for production Redis."""
    if not _redis:
        return []
    keys = []
    try:
        async for key in _redis.scan_iter(match=pattern, count=100):
            keys.append(key)
    except Exception as e:
        LOGGER.warning(f"Redis SCAN error [{pattern}]: {e}")
    return keys
async def check_memory_and_purge():
    """Smart memory management: Purges old keys if memory exceeds limit."""
    if not _redis: return
    try:
        info = await _redis.info("memory")
        used = int(info.get("used_memory", 0))
        if used > MEM_LIMIT_BYTES:
            LOGGER.warning(f"Redis memory usage high ({used/1024/1024:.2f}MB). Purging old caches...")
            # Purge short-lived user caches and leaderboard entries
            keys = (await _scan_keys("user:*")) + (await _scan_keys("lb:*")) + (await _scan_keys("rank:*"))
            if keys:
                await _redis.delete(*keys[:50]) # Delete batches
    except Exception as e: LOGGER.debug(f"Purge error: {e}")
async def rdel(*keys: str):
    """Delete one or more keys from Redis. Silently ignores errors."""
    if not _redis or not keys:
        return
    try:
        await _redis.delete(*keys)
    except Exception as e:
        LOGGER.warning(f"Redis DEL error {keys}: {e}")
async def rget_json(key: str) -> Optional[Any]:
    raw = await rget(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None
async def rset_json(key: str, value: Any, ttl: int):
    try:
        await rset(key, json.dumps(value, default=str), ttl)
    except Exception as e:
        LOGGER.warning(f"Redis SET_JSON error [{key}]: {e}")
def _cooldown_key(domain: str, user_id: int) -> str:
    return f"cooldown:{domain}:{user_id}"
async def is_on_cooldown(domain: str, user_id: int, duration: int) -> tuple[bool, int]:
    """
    Check & set a Redis-based cooldown.
    Returns (is_on_cooldown, seconds_remaining).
    Uses SET NX EX to atomically acquire if not present.
    """
    if not _redis:
        return False, 0
    key = _cooldown_key(domain, user_id)
    try:
        # SET key 1 EX duration NX — only sets if key doesn't exist
        # Wrapped in wait_for to prevent silent hangs
        result = await asyncio.wait_for(_redis.set(key, "1", ex=duration, nx=True), timeout=2.5)
        if result:
            # Key was newly set → not on cooldown
            return False, 0
        # Key already existed → on cooldown
        ttl = await asyncio.wait_for(_redis.ttl(key), timeout=2.5)
        return True, max(0, ttl)
    except asyncio.TimeoutError:
        LOGGER.warning(f"Redis cooldown timeout [{key}]. Failsafe: Allow access.")
        return False, 0
    except Exception as e:
        LOGGER.warning(f"Redis cooldown error [{key}]: {e}")
        return False, 0
async def reset_cooldown(domain: str, user_id: int):
    """Force-remove a cooldown (e.g., for owner bypass)."""
    await rdel(_cooldown_key(domain, user_id))
def _lb_key(metric: str, limit: int = 10) -> str:
    return f"lb:{metric}:{limit}"
async def get_cached_leaderboard(metric: str, limit: int = 10) -> Optional[list]:
    return await rget_json(_lb_key(metric, limit))
async def set_cached_leaderboard(metric: str, data: list, limit: int = 10):
    await rset_json(_lb_key(metric, limit), data, TTL_LEADERBOARD)
# --- USER & BALANCE CACHING ---
async def invalidate_user_cache(user_id: int):
    """Remove user and balance strings from Redis."""
    if not _redis: return
    await rdel(f"user:{user_id}", f"balance:{user_id}")
async def get_cached_user(user_id: int) -> Optional[dict]:
    return await rget_json(f"user:{user_id}")
async def set_cached_user(user_id: int, user_data: dict):
    await rset_json(f"user:{user_id}", user_data, TTL_USER)
async def get_cached_balance(user_id: int) -> Optional[int]:
    return await rget_json(f"balance:{user_id}")
async def set_cached_balance(user_id: int, balance: int):
    await rset_json(f"balance:{user_id}", balance, TTL_USER)
# --- DAILY & WEEKLY COOLDOWNS ---
async def get_daily_date(user_id: int) -> Optional[str]:
    return await rget(f"daily:{user_id}")
async def set_daily_date(user_id: int, date_str: str):
    await rset(f"daily:{user_id}", date_str, TTL_DAILY)
async def get_weekly_date(user_id: int) -> Optional[str]:
    return await rget(f"weekly:{user_id}")
async def set_weekly_date(user_id: int, date_str: str):
    await rset(f"weekly:{user_id}", date_str, TTL_WEEKLY)
# --- LEADERBOARD CACHE INVALIDATION ---
async def invalidate_leaderboard_cache(metric: str = None):
    """Clear specific or all leaderboard caches in Redis."""
    if not _redis: return
    if metric:
        await rdel(_lb_key(metric, 10))
    else:
        keys = await _scan_keys("lb:*")
        if keys: await rdel(*keys)
# --- SESSION MANAGEMENT (BOT) ---
def _session_key(session_id: str) -> str:
    return f"session:{session_id}"
async def create_session(session_id: str, data: dict, ttl: int = TTL_SESSION):
    """Create a temporary session for multi-step bot flows."""
    await rset_json(_session_key(session_id), data, ttl)
async def get_session(session_id: str) -> Optional[dict]:
    return await rget_json(_session_key(session_id))
async def delete_session(session_id: str):
    await rdel(_session_key(session_id))
def _zset_key(metric: str) -> str:
    # Map metrics to Redis keys
    mapping = {
        "level": "user_xp_leaderboard",
        "harem": "user_harem_leaderboard",
        "shards": "user_shards_leaderboard",
        "zenith": "user_zenith_leaderboard",
        "guesses": "user_guesses_leaderboard"
    }
    return mapping.get(metric, f"user_{metric}_leaderboard")
async def update_user_rank(user_id: int, score: int, metric: str = "level"):
    """Update user score in the specific metric's ZSET and CAP it for memory."""
    if not _redis: return
    key = _zset_key(metric)
    try:
        await _redis.zadd(key, {str(user_id): score})
        # SMART: Only keep the top 1000 in the fast cache to stay within 30MB
        await _redis.zremrangebyrank(key, 0, -1001)
    except Exception as e:
        LOGGER.warning(f"Redis ZSET update error [{metric}]: {e}")
async def get_user_rank(user_id: int, metric: str = "level") -> Optional[int]:
    """Get 1-based rank from metric ZSET. Returns None on miss."""
    if not _redis: return None
    key = _zset_key(metric)
    try:
        rank = await _redis.zrevrank(key, str(user_id))
        return (rank + 1) if rank is not None else None
    except Exception:
        return None
async def get_total_ranked_users(metric: str = "level") -> int:
    if not _redis: return 0
    key = _zset_key(metric)
    try: return await _redis.zcard(key)
    except Exception: return 0
# FIX: Create the lock at module level — no lazy init, no global mutation needed.
# asyncio.Lock() is safe to instantiate at module level in Python 3.10+.
_rebuild_lock = asyncio.Lock()
async def rebuild_leaderboard(user_collection, metric: str = "level"):
    """
    Cold-rebuild a specific Redis ZSET from MongoDB with memory safety.
    Uses an atomic Rename-Swap pattern to prevent empty leaderboard states.
    """
    async with _rebuild_lock:
        if not _redis: return
        key = _zset_key(metric)
        temp_key = f"temp:{key}"
        # Metric mapping to Mongo fields
        mongo_fields = {
            "level": "xp",
            "harem": "char_count",
            "shards": "balance",
            "zenith": "zenith",
            "guesses": "guess_count"
        }
        field = mongo_fields.get(metric, "xp")
        try:
            LOGGER.info(f"Starting safe {metric} ZSET rebuild from MongoDB...")
            # Clean up any leftover temp key first
            await _redis.delete(temp_key)
            # Get Top 1,000 users by specific field descending
            cursor = user_collection.find({field: {"$gt": 0}}, {"id": 1, field: 1}).sort(field, -1).limit(1000)
            batch = {}
            count = 0
            async for user in cursor:
                uid = str(user.get("id"))
                score = user.get(field, 0)
                if uid and score:
                    batch[uid] = score
                    count += 1
                if len(batch) >= 100:
                    await _redis.zadd(temp_key, batch)
                    batch = {}
            if batch:
                await _redis.zadd(temp_key, batch)
            
            # If we populated entries, atomically rename temp_key to key.
            if count > 0:
                await _redis.rename(temp_key, key)
            else:
                # If no users had scores, clear the leaderboard
                await _redis.delete(key)
                await _redis.delete(temp_key)
                
            LOGGER.info(f"{metric} ZSET rebuild complete. Synchronized {count} top users.")
        except Exception as e:
            LOGGER.error(f"Failed to rebuild {metric} ZSET: {e}")
            # Failsafe cleanup of temp key
            try:
                await _redis.delete(temp_key)
            except Exception:
                pass
async def sync_user_to_redis(user_id: int, user_doc: dict = None):
    """
    Synchronizes a user's critical metrics (Level, Harem, Balance, Zenith, Guesses) 
    to Redis ZSETs instantly. Used after major state changes to prevent drift.
    """
    if not _redis: return
    if not user_doc:
        from Grabber.database import user_collection
        user_doc = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user_doc: return
    uid_str = str(user_id)
    try:
        pipe = _redis.pipeline()
        # 1. Update all leaderboard scores
        pipe.zadd(_zset_key("level"),   {uid_str: user_doc.get("xp", 0)})
        pipe.zadd(_zset_key("harem"),   {uid_str: user_doc.get("char_count", 0)})
        pipe.zadd(_zset_key("shards"),  {uid_str: user_doc.get("balance", 0)})
        pipe.zadd(_zset_key("zenith"),  {uid_str: user_doc.get("zenith", 0)})
        pipe.zadd(_zset_key("guesses"), {uid_str: user_doc.get("guess_count", 0)})
        # 2. Invalidate string caches
        pipe.delete(f"user:{user_id}", f"balance:{user_id}")
        await pipe.execute()
    except Exception as e:
        LOGGER.warning(f"Failed to sync user {user_id} to Redis: {e}")
_GAMEBOT_KEY = "gamebot_groups"
async def refresh_gamebot_groups_cache(gamebot_enabled_groups_collection) -> set:
    """Load enabled groups from MongoDB and cache in Redis set."""
    groups = await gamebot_enabled_groups_collection.find({}, {"chat_id": 1}).to_list(length=1000)
    ids = {str(g["chat_id"]) for g in groups}
    if _redis and ids:
        try:
            pipe = _redis.pipeline()
            pipe.delete(_GAMEBOT_KEY)
            pipe.sadd(_GAMEBOT_KEY, *ids)
            pipe.expire(_GAMEBOT_KEY, TTL_GAMEBOT)
            await pipe.execute()
        except Exception as e:
            LOGGER.warning(f"Redis gamebot set error: {e}")
    return ids
async def is_gamebot_enabled(chat_id: int, gamebot_enabled_groups_collection) -> bool:
    """Check if a chat has gamebot enabled. Uses Redis set, falls back to MongoDB."""
    if _redis:
        try:
            exists = await _redis.sismember(_GAMEBOT_KEY, str(chat_id))  # type: ignore
            if exists:
                return True
            # Key might be expired — check if key exists at all
            key_exists = await _redis.exists(_GAMEBOT_KEY)
            if key_exists:
                return False  # Key exists but chat not in set → definitely disabled
        except Exception as e:
            LOGGER.warning(f"Redis gamebot check error: {e}")
    # MongoDB fallback
    result = await gamebot_enabled_groups_collection.find_one({"chat_id": chat_id})
    return result is not None
async def add_gamebot_group(chat_id: int):
    """Add a group to the gamebot enabled set in Redis."""
    if _redis:
        try:
            await _redis.sadd(_GAMEBOT_KEY, str(chat_id))  # type: ignore
        except Exception as e:
            LOGGER.warning(f"Redis gamebot add error: {e}")
async def remove_gamebot_group(chat_id: int):
    """Remove a group from the gamebot enabled set in Redis."""
    if _redis:
        try:
            await _redis.srem(_GAMEBOT_KEY, str(chat_id))  # type: ignore
        except Exception as e:
            LOGGER.warning(f"Redis gamebot remove error: {e}")
