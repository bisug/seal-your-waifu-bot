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

# ── TTLs (seconds) ──────────────────────────────────────────────
TTL_USER        = 300     # 5 minutes
TTL_LEADERBOARD = 300     # 5 minutes
TTL_SESSION     = 3600    # 1 hour
TTL_DAILY       = 48 * 3600
TTL_WEEKLY      = 8 * 24 * 3600
TTL_GAMEBOT     = 600     # 10 minutes


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
        await _redis.setex(key, ttl, value)
    except Exception as e:
        LOGGER.warning(f"Redis SET error [{key}]: {e}")

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

async def invalidate_leaderboard_cache():
    """Invalidate all leaderboard entries. Call after balance/character writes."""
    if not _redis:
        return
    try:
        keys = await _redis.keys("lb:*")
        if keys:
            await _redis.delete(*keys)
    except Exception as e:
        LOGGER.warning(f"Redis leaderboard invalidation error: {e}")


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
