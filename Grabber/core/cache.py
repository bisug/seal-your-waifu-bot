"""
Centralized Redis cache layer for Seal-Bot.

All methods are safe-by-default: if Redis is unavailable (r is None or raises),
callers receive None and fall back to MongoDB. This ensures the bot works even
if Redis goes down.

Key prefixes:
  user:{id}          → full user document JSON, TTL 5m
  balance:{id}       → int shard balance, TTL 5m
  cooldown:{key}     → Unix timestamp float, TTL = cooldown duration
  lb:{metric}        → leaderboard JSON list, TTL 5m
  session:{id}       → session JSON, TTL = caller-specified (default 1h)
  gamebot_groups     → Redis set of enabled chat_ids, TTL 10m
  daily:{id}         → last daily date string YYYY-MM-DD, TTL 48h
  weekly:{id}        → last weekly date string YYYY-MM-DD, TTL 8d
"""

import json
import time
from typing import Any, Optional, List
from Grabber.database import r as _redis
from Grabber import LOGGER

# ── TTLs (seconds) optimized for 30MB ──────────────────────────
TTL_USER        = 60      # 1 minute (Fast refresh to save space)
TTL_LEADERBOARD = 300     # 5 minutes
TTL_SESSION     = 1800    # 30 minutes
TTL_DAILY       = 24 * 3600 # 24h
TTL_WEEKLY      = 7 * 24 * 3600
TTL_GAMEBOT     = 300     # 5 minutes
MEM_LIMIT_BYTES = 25 * 1024 * 1024 # 25MB Soft limit for auto-purge


# ── Low-level helpers ────────────────────────────────────────────

async def rget(key: str) -> Optional[str]:
    """Get a string value from Redis. Returns None on miss or error."""
    if not _redis:
        return None
    try:
        return await _redis.get(key)
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
        await _redis.setex(key, ttl, value)
    except Exception as e:
        LOGGER.warning(f"Redis SET error [{key}]: {e}")

async def check_memory_and_purge():
    """Smart memory management: Purges old keys if memory exceeds limit."""
    if not _redis: return
    try:
        info = await _redis.info("memory")
        used = int(info.get("used_memory", 0))
        if used > MEM_LIMIT_BYTES:
            LOGGER.warning(f"Redis memory usage high ({used/1024/1024:.2f}MB). Purging old caches...")
            # Purge short-lived user caches and leaderboard entries
            keys = await _redis.keys("user:*") + await _redis.keys("lb:*") + await _redis.keys("rank:*")
            if keys:
                await _redis.delete(*keys[:50]) # Delete batches
    except Exception: pass

async def rdel(*keys: str):
    """Delete one or more keys from Redis. Silently ignores errors."""
    if not _redis or not keys:
        return
    try:
        await _redis.delete(*keys)
    except Exception as e:
        LOGGER.warning(f"Redis DEL error {keys}: {e}")


# ── JSON helpers ─────────────────────────────────────────────────

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


# ── User cache ───────────────────────────────────────────────────

def _user_key(user_id: int) -> str:
    return f"user:{user_id}"

def _balance_key(user_id: int) -> str:
    return f"balance:{user_id}"

async def get_cached_user(user_id: int) -> Optional[dict]:
    """Return cached user document or None."""
    return await rget_json(_user_key(user_id))

async def set_cached_user(user_id: int, user_doc: dict):
    """Cache a user document for TTL_USER seconds."""
    await rset_json(_user_key(user_id), user_doc, TTL_USER)

async def invalidate_user_cache(user_id: int):
    """Remove user + balance cache entries. Call after any write to user doc."""
    await rdel(_user_key(user_id), _balance_key(user_id))

async def get_cached_balance(user_id: int) -> Optional[int]:
    """Return cached shard balance or None."""
    raw = await rget(_balance_key(user_id))
    return int(raw) if raw is not None else None

async def set_cached_balance(user_id: int, balance: int):
    await rset(_balance_key(user_id), str(balance), TTL_USER)


# ── Cooldown helpers (replaces in-memory dicts) ──────────────────

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
        result = await _redis.set(key, "1", ex=duration, nx=True)
        if result:
            # Key was newly set → not on cooldown
            return False, 0
        # Key already existed → on cooldown
        ttl = await _redis.ttl(key)
        return True, max(0, ttl)
    except Exception as e:
        LOGGER.warning(f"Redis cooldown error [{key}]: {e}")
        return False, 0

async def reset_cooldown(domain: str, user_id: int):
    """Force-remove a cooldown (e.g., for owner bypass)."""
    await rdel(_cooldown_key(domain, user_id))


# ── Daily / Weekly claim timestamps ──────────────────────────────

def _daily_key(user_id: int) -> str:
    return f"daily:{user_id}"

def _weekly_key(user_id: int) -> str:
    return f"weekly:{user_id}"

async def get_daily_date(user_id: int) -> Optional[str]:
    return await rget(_daily_key(user_id))

async def set_daily_date(user_id: int, date_str: str):
    await rset(_daily_key(user_id), date_str, TTL_DAILY)

async def get_weekly_date(user_id: int) -> Optional[str]:
    return await rget(_weekly_key(user_id))

async def set_weekly_date(user_id: int, date_str: str):
    await rset(_weekly_key(user_id), date_str, TTL_WEEKLY)


# ── Leaderboard cache ────────────────────────────────────────────

def _lb_key(metric: str) -> str:
    return f"lb:{metric}"

async def get_cached_leaderboard(metric: str) -> Optional[list]:
    return await rget_json(_lb_key(metric))

async def set_cached_leaderboard(metric: str, data: list):
    await rset_json(_lb_key(metric), data, TTL_LEADERBOARD)

# ── Unified XP Ranking (ZSET) ──────────────────────────────────

_RANK_KEY = "user_xp_leaderboard"

async def update_user_rank(user_id: int, xp: int):
    """Update user score in the global ZSET and CAP it to Top 500 for memory."""
    if not _redis: return
    try:
        await _redis.zadd(_RANK_KEY, {str(user_id): xp})
        # SMART: Only keep the top 500 in the fast cache to stay within 30MB
        await _redis.zremrangebyrank(_RANK_KEY, 0, -501)
    except Exception as e:
        LOGGER.warning(f"Redis ZSET update error: {e}")

async def get_user_rank(user_id: int) -> Optional[int]:
    """Get 1-based rank from ZSET. Returns None on miss."""
    if not _redis: return None
    try:
        rank = await _redis.zrevrank(_RANK_KEY, str(user_id))
        return (rank + 1) if rank is not None else None
    except Exception:
        return None

async def get_total_ranked_users() -> int:
    if not _redis: return 0
    try: return await _redis.zcard(_RANK_KEY)
    except Exception: return 0

async def rebuild_leaderboard(user_collection):
    """
    Cold-rebuild the Redis XP ZSET from MongoDB with 30MB memory safety.
    Only pulls Top 1,000 users to keep the fast cache small.
    """
    if not _redis: return
    try:
        LOGGER.info("Starting safe XP ZSET rebuild from MongoDB (Top 1000)...")
        # Get Top 1,000 users by XP descending
        cursor = user_collection.find({"xp": {"$gt": 0}}, {"id": 1, "xp": 1}).sort("xp", -1).limit(1000)
        
        # Clear the old set first
        await _redis.delete(_RANK_KEY)
        
        batch = {}
        count = 0
        async for user in cursor:
            uid = str(user.get("id"))
            xp = user.get("xp", 0)
            if uid and xp:
                batch[uid] = xp
                count += 1
            
            # Batch write every 100 users for performance
            if len(batch) >= 100:
                await _redis.zadd(_RANK_KEY, batch)
                batch = {}
        
        # Final batch
        if batch:
            await _redis.zadd(_RANK_KEY, batch)
            
        LOGGER.info(f"XP ZSET rebuild complete. Synchronized {count} top users.")
    except Exception as e:
        LOGGER.error(f"Failed to rebuild XP ZSET in memory-safe mode: {e}")


# ── Sessions (replaces MongoDB sessions) ─────────────────────────

def _session_key(session_id: str) -> str:
    return f"session:{session_id}"

async def create_session(session_id: str, data: dict, ttl: int = TTL_SESSION):
    """Store a session in Redis with TTL. Falls back to MongoDB if Redis unavailable."""
    if _redis:
        await rset_json(_session_key(session_id), data, ttl)
    else:
        # MongoDB fallback
        from Grabber.database import sessions_collection
        import time as _time
        data["_id"] = session_id
        data["created_at"] = _time.time()
        await sessions_collection.replace_one({"_id": session_id}, data, upsert=True)

async def get_session(session_id: str) -> Optional[dict]:
    """Retrieve session from Redis, falling back to MongoDB."""
    if _redis:
        result = await rget_json(_session_key(session_id))
        if result is not None:
            return result
    # MongoDB fallback
    from Grabber.database import sessions_collection
    return await sessions_collection.find_one({"_id": session_id})

async def delete_session(session_id: str):
    """Delete a session from Redis and MongoDB."""
    if _redis:
        await rdel(_session_key(session_id))
    from Grabber.database import sessions_collection
    await sessions_collection.delete_one({"_id": session_id})


# ── Nguess enabled groups set ─────────────────────────────────────

_GAMEBOT_KEY = "gamebot_groups"

async def refresh_gamebot_groups_cache(gamebot_enabled_groups_collection) -> set:
    """Load enabled groups from MongoDB and cache in Redis set."""
    groups = await gamebot_enabled_groups_collection.find({}, {"chat_id": 1}).to_list(length=1000)
    ids = {str(g["chat_id"]) for g in groups}
    if _redis and ids:
        try:
            pipe = _redis.pipeline()
            await pipe.delete(_GAMEBOT_KEY)
            await pipe.sadd(_GAMEBOT_KEY, *ids)
            await pipe.expire(_GAMEBOT_KEY, TTL_GAMEBOT)
            await pipe.execute()
        except Exception as e:
            LOGGER.warning(f"Redis gamebot set error: {e}")
    return ids

async def is_gamebot_enabled(chat_id: int, gamebot_enabled_groups_collection) -> bool:
    """Check if a chat has gamebot enabled. Uses Redis set, falls back to MongoDB."""
    if _redis:
        try:
            exists = await _redis.sismember(_GAMEBOT_KEY, str(chat_id))
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
            await _redis.sadd(_GAMEBOT_KEY, str(chat_id))
        except Exception as e:
            LOGGER.warning(f"Redis gamebot add error: {e}")

async def remove_gamebot_group(chat_id: int):
    """Remove a group from the gamebot enabled set in Redis."""
    if _redis:
        try:
            await _redis.srem(_GAMEBOT_KEY, str(chat_id))
        except Exception as e:
            LOGGER.warning(f"Redis gamebot remove error: {e}")
