"""Leaderboard ZSET layer: per-metric rankings in Redis plus rebuild/sync.

Imported by progression, user, leaderboard UI, and the webapp. The plain
string-cache helpers (rget/rset/...) live in backend.core.cache.
"""
import asyncio
import json
import time
from typing import Optional

from backend.core.constants import METRICS
from backend.core.logging import get_logger
from backend.database import r as _redis

LOGGER = get_logger(__name__)


def _zset_key(metric: str) -> str:
    # The "level" metric is keyed by its Mongo field name (xp); all other
    # metrics use their own name.
    name = "xp" if metric == "level" else metric
    return f"user_{name}_leaderboard"

# Metrics whose ZSET may have drifted from Mongo (e.g. an instant sync
# failed). The periodic rebuild skips clean metrics to avoid hourly full
# rebuilds when sync_user_to_redis already keeps the ZSETs fresh.
_ALL_LB_METRICS = ("level", "harem", "shards", "zenith", "guesses")
_lb_dirty_metrics: set[str] = set()


def mark_leaderboard_dirty(metrics=None):
    """Flag leaderboard metrics as needing a rebuild from Mongo."""
    if metrics is None:
        _lb_dirty_metrics.update(_ALL_LB_METRICS)
    else:
        _lb_dirty_metrics.update(metrics)


def consume_leaderboard_dirty(metric: str) -> bool:
    """Return True (and clear the flag) if the metric needs a rebuild."""
    if metric in _lb_dirty_metrics:
        _lb_dirty_metrics.discard(metric)
        return True
    return False


async def update_user_rank(user_id: int, score: int, metric: str = "level"):
    """Update user score in the specific metric's ZSET and CAP it for memory."""
    if not _redis: return
    key = _zset_key(metric)
    try:
        await _redis.zadd(key, {str(user_id): score})
        # Only keep the top 1000 in the fast cache to stay within 30MB
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
    """Count of users tracked in a metric's Redis ZSET (0 if Redis is down)."""
    if not _redis: return 0
    key = _zset_key(metric)
    try: return await _redis.zcard(key)
    except Exception: return 0

# Create the lock at module level — no lazy init, no global mutation needed.
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
        field = METRICS.get(metric, METRICS["level"])["field"]
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
            await publish_leaderboard_update()
        except Exception as e:
            LOGGER.error(f"Failed to rebuild {metric} ZSET: {e}")
            # Failsafe cleanup of temp key
            try:
                await _redis.delete(temp_key)
            except Exception:
                pass

_lb_publish_throttle = 0.0


async def publish_leaderboard_update():
    """Notify /ws/leaderboard subscribers that standings changed. Throttled
    to one broadcast per 15s — sync_user_to_redis fires on every state change
    and unthrottled publishing would flood subscribers."""
    global _lb_publish_throttle
    if not _redis: return
    now = time.monotonic()
    if now - _lb_publish_throttle < 15:
        return
    _lb_publish_throttle = now
    try:
        payload = json.dumps({"type": "leaderboard_update", "ts": int(time.time())})
        await asyncio.wait_for(_redis.publish("leaderboard_updates", payload), timeout=2.0)
    except Exception:
        pass  # Failsafe: realtime is best-effort, never break the write path.


async def sync_user_to_redis(user_id: int, user_doc: dict = None):
    """
    Synchronizes a user's critical metrics (Level, Harem, Balance, Prisms, Guesses)
    to Redis ZSETs instantly. Used after major state changes to prevent drift.
    """
    if not _redis: return
    if not user_doc:
        from backend.database import user_collection
        user_doc = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user_doc: return
    uid_str = str(user_id)
    try:
        pipe = _redis.pipeline()
        pipe.zadd(_zset_key("level"),   {uid_str: user_doc.get("xp", 0)})
        pipe.zadd(_zset_key("harem"),   {uid_str: user_doc.get("char_count", 0)})
        pipe.zadd(_zset_key("shards"),  {uid_str: user_doc.get("balance", 0)})
        pipe.zadd(_zset_key("zenith"),  {uid_str: user_doc.get("zenith", 0)})
        pipe.zadd(_zset_key("guesses"), {uid_str: user_doc.get("guess_count", 0)})
        pipe.delete(f"user:{user_id}", f"balance:{user_id}")
        await pipe.execute()
        await publish_leaderboard_update()
    except Exception as e:
        LOGGER.warning(f"Failed to sync user {user_id} to Redis: {e}")
        # Instant sync failed — the periodic rebuild must repair the drift.
        mark_leaderboard_dirty()
