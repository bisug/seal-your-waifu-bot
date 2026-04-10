import asyncio
import logging
from datetime import datetime, timedelta
from Grabber.database import user_collection
from Grabber.core.cache import sync_user_to_redis, _redis
from Grabber import LOGGER

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
                keys = []
                async for key in _redis.scan_iter(match="rate_limit:*", count=100):
                    keys.append(key)
                if keys:
                    # Redis should expire them, but this ensures cleanup if TTL failed
                    LOGGER.info(f"Persistence Worker: Cleaned up {len(keys)} rate limit keys.")
            
        except Exception as e:
            LOGGER.error(f"Persistence Worker Error: {e}")
            
        # Wait 6 hours
        await asyncio.sleep(6 * 3600)

async def prune_legacy_eggs():
    """
    Converts legacy string-based eggs (e.g. 'common') into proper dict objects
    to ensure WebApp compatibility.
    """
    cursor = user_collection.find({"eggs": {"$elemMatch": {"$type": "string"}}})
    count = 0
    async for user in cursor:
        uid = user["id"]
        eggs = user.get("eggs", [])
        new_eggs = []
        modified = False
        
        for idx, egg in enumerate(eggs):
            if isinstance(egg, str):
                from Grabber.modules.economy.hunt import TIER_MAP, EGG_TIERS
                tier = TIER_MAP.get(egg, egg)
                tier_info = EGG_TIERS.get(tier, EGG_TIERS["common"])
                new_eggs.append({
                    "id": f"mig_{int(datetime.now().timestamp())}_{idx}",
                    "tier": tier,
                    "name": tier_info["name"],
                    "status": "fresh",
                    "obtained_at": user.get("created_at") or datetime.now()
                })
                modified = True
            else:
                new_eggs.append(egg)
        
        if modified:
            await user_collection.update_one({"id": uid}, {"$set": {"eggs": new_eggs}})
            count += 1
            
    if count > 0:
        LOGGER.info(f"Persistence Worker: Pruned legacy eggs for {count} users.")

async def verify_top_users_consistency():
    """
    Checks the denormalized char_count against len(characters) for top users
    and fixes any discrepancies.
    """
    # Check top 50 by char_count
    cursor = user_collection.find({}).sort("char_count", -1).limit(50)
    fixed = 0
    async for user in cursor:
        actual_count = len(user.get("characters") or [])
        stored_count = user.get("char_count", 0)
        
        if actual_count != stored_count:
            uid = user["id"]
            await user_collection.update_one({"id": uid}, {"$set": {"char_count": actual_count}})
            await sync_user_to_redis(uid)
            fixed += 1
            
    if fixed > 0:
        LOGGER.info(f"Persistence Worker: Fixed char_count drift for {fixed} users.")
