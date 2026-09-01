"""Centralized Redis cache layer. All methods are failsafe (fall back to MongoDB).
Key prefixes: user, balance, cooldown, lb.
Sessions live in backend.core.sessions; leaderboard ZSETs in backend.core.leaderboard.
"""
import asyncio
import json
import time
from typing import Any, Optional

# Back-compat re-exports: these moved to their own modules.
from backend.core.leaderboard import (  # noqa: F401
    consume_leaderboard_dirty,
    get_total_ranked_users,
    get_user_rank,
    mark_leaderboard_dirty,
    publish_leaderboard_update,
    rebuild_leaderboard,
    sync_user_to_redis,
    update_user_rank,
)
from backend.core.logging import get_logger
from backend.database import r as _redis
from config import config

LOGGER = get_logger(__name__)
r = _redis
# TTL settings (seconds)
TTL_USER        = 60
TTL_LEADERBOARD = 300
TTL_SESSION     = 1800
TTL_DAILY       = 86400
TTL_WEEKLY      = 604800
DEFAULT_REDIS_AUTO_LIMIT_BYTES = 64 * 1024 * 1024
VOLATILE_CACHE_PATTERNS = ("user:*", "balance:*", "lb:*", "rank:*")
_last_memory_check = 0.0


def _redis_memory_limit_bytes(info: dict) -> tuple[int, str]:
    configured_mb = int(getattr(config, "REDIS_MEMORY_LIMIT_MB", 0))
    if configured_mb > 0:
        return configured_mb * 1024 * 1024, "configured"

    try:
        maxmemory = int(info.get("maxmemory") or 0)
    except (TypeError, ValueError):
        maxmemory = 0
    if maxmemory > 0:
        return max(1, int(maxmemory * 0.80)), "redis_maxmemory"

    return DEFAULT_REDIS_AUTO_LIMIT_BYTES, "auto_default"

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
    """Purge volatile keys when Redis memory exceeds the limit (rate-limited to 1/min)."""
    if not _redis: return
    global _last_memory_check
    now = time.monotonic()
    if now - _last_memory_check < 60:
        return
    _last_memory_check = now
    try:
        info = await asyncio.wait_for(_redis.info("memory"), timeout=3.0)
        used = int(info.get("used_memory", 0))
        limit, source = _redis_memory_limit_bytes(info)
        if used > limit:
            LOGGER.warning(
                "Redis memory usage high (used=%.2fMB limit=%.2fMB source=%s). Purging old caches...",
                used / 1024 / 1024,
                limit / 1024 / 1024,
                source,
            )
            deleted = await purge_volatile_redis_caches(max_keys=config.RESOURCE_REDIS_PURGE_BATCH_SIZE)
            if deleted:
                LOGGER.info("Redis volatile cache purge removed %s key(s).", deleted)
    except Exception as e: LOGGER.debug(f"Purge error: {e}")


async def purge_volatile_redis_caches(
    *,
    max_keys: int | None = None,
    patterns: tuple[str, ...] = VOLATILE_CACHE_PATTERNS,
) -> int:
    """Delete bounded batches of volatile cache keys without scanning into memory."""
    if not _redis:
        return 0
    limit = max_keys if max_keys and max_keys > 0 else config.RESOURCE_REDIS_PURGE_BATCH_SIZE
    deleted = 0
    batch: list[str] = []

    async def flush_batch() -> None:
        nonlocal deleted, batch
        if not batch:
            return
        try:
            deleted += int(await asyncio.wait_for(_redis.delete(*batch), timeout=3.0))
        except Exception as e:
            LOGGER.warning(f"Redis volatile purge delete failed: {e}")
        finally:
            batch = []

    try:
        for pattern in patterns:
            async for key in _redis.scan_iter(match=pattern, count=100):
                batch.append(key)
                if len(batch) >= 50 or deleted + len(batch) >= limit:
                    await flush_batch()
                if deleted >= limit:
                    return deleted
        await flush_batch()
    except Exception as e:
        LOGGER.warning(f"Redis volatile purge scan failed: {e}")
    return deleted
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
