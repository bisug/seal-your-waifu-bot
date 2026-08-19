import asyncio
from backend.core.eggs import get_egg_tier_info
from backend import LOGGER
from backend.core.cache import _redis, sync_user_to_redis
from backend.core.utils import get_now_utc, get_user_id_query
from backend.database import user_collection
async def background_maintenance():
    """
    Main loop for background maintenance tasks.
    Runs every 6 hours.
    """
    LOGGER.info("Persistence Worker: Starting background maintenance...")
    while True:
        try:
            # 1. Prune legacy string-based eggs
            await prune_legacy_eggs()
            # 2. Verify and fix char_count for TOP 100 users (precautionary)
            await verify_top_users_consistency()
            # 3. Clean up stale Redis rate limits
            if _redis:
                deleted = 0
                async for key in _redis.scan_iter(match="rate_limit:*", count=100):
                    ttl = await _redis.ttl(key)
                    if ttl == -1:
                        await _redis.delete(key)
                        deleted += 1
                if deleted:
                    LOGGER.info(f"Persistence Worker: Cleaned up {deleted} rate limit keys without TTL.")
        except Exception as e:
            LOGGER.error(f"Persistence Worker Error: {e}")
        # Wait 6 hours
        await asyncio.sleep(6 * 3600)
_legacy_egg_empty_runs = 0
_LEGACY_EGG_SKIP_AFTER = 3


async def prune_legacy_eggs():
    """
    Converts legacy string-based eggs (e.g. 'common') into proper dict objects
    to ensure WebApp compatibility.
    """
    global _legacy_egg_empty_runs
    # The query is an unindexed collection scan; once the migration is done,
    # stop paying for it every 6 hours.
    if _legacy_egg_empty_runs >= _LEGACY_EGG_SKIP_AFTER:
        return
    cursor = user_collection.find({"eggs": {"$elemMatch": {"$type": "string"}}})
    count = 0
    async for user in cursor:
        uid = user["id"]
        eggs = user.get("eggs", [])
        new_eggs = []
        modified = False
        for idx, egg in enumerate(eggs):
            if isinstance(egg, str):
                now = get_now_utc()
                tier, tier_info = get_egg_tier_info(egg)
                new_eggs.append({
                    "id": f"mig_{int(now.timestamp())}_{idx}",
                    "tier": tier,
                    "name": tier_info["name"],
                    "status": "fresh",
                    "is_corrupted": False,
                    "obtained_at": user.get("created_at") or now
                })
                modified = True
            else:
                new_eggs.append(egg)
        if modified:
            await user_collection.update_one(get_user_id_query(uid), {"$set": {"eggs": new_eggs}})
            count += 1
    if count > 0:
        _legacy_egg_empty_runs = 0
        LOGGER.info(f"Persistence Worker: Pruned legacy eggs for {count} users.")
    else:
        _legacy_egg_empty_runs += 1
        if _legacy_egg_empty_runs >= _LEGACY_EGG_SKIP_AFTER:
            LOGGER.info(
                "Persistence Worker: no legacy eggs for %d consecutive runs; disabling scan.",
                _LEGACY_EGG_SKIP_AFTER,
            )
async def verify_top_users_consistency():
    """
    Checks the denormalized char_count against len(characters) for top users
    and fixes any discrepancies.
    """
    # Check top 50 by char_count
    # Use {$exists: true} so MongoDB can use the sparse char_count index.
    # find({}).sort() on a sparse index may fall back to a full collection scan.
    # $size computes the real count server-side so huge character arrays are
    # never transferred to the worker.
    cursor = user_collection.aggregate([
        {"$match": {"char_count": {"$exists": True}}},
        {"$sort": {"char_count": -1}},
        {"$limit": 50},
        {"$project": {
            "id": 1,
            "char_count": 1,
            "actual_count": {"$size": {"$ifNull": ["$characters", []]}},
        }},
    ])
    fixed = 0
    async for user in cursor:
        actual_count = user.get("actual_count", 0)
        stored_count = user.get("char_count", 0)
        if actual_count != stored_count:
            uid = user["id"]
            await user_collection.update_one(get_user_id_query(uid), {"$set": {"char_count": actual_count}})
            await sync_user_to_redis(uid)
            fixed += 1
    if fixed > 0:
        LOGGER.info(f"Persistence Worker: Fixed char_count drift for {fixed} users.")
