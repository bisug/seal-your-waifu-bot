from typing import Optional

from Grabber.core.cache import (get_cached_balance, invalidate_user_cache,
                                set_cached_balance)
from Grabber.database import user_collection


async def get_user_balance(user_id: int) -> int:
    """
    Fetch the current shard balance for a user.
    Checks Redis cache first; falls back to MongoDB.
    """
    cached = await get_cached_balance(user_id)
    if cached is not None:
        return cached
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}}, {"balance": 1})
    balance = user.get("balance", 0) if user else 0
    await set_cached_balance(user_id, balance)
    return balance

async def update_user_balance(user_id: int, amount: int):
    """
    Increment or decrement a user's balance, then invalidate cache.
    """
    await user_collection.update_one(
        {"id": {"$in": [user_id, str(user_id)]}},
        {"$inc": {"balance": amount}},
        upsert=True
    )
    await invalidate_user_cache(user_id)

async def check_and_deduct(user_id: int, amount: int) -> bool:
    """
    Atomically check balance and deduct. Invalidates cache on success.
    Returns True if successful, False otherwise.
    """
    result = await user_collection.update_one(
        {"id": {"$in": [user_id, str(user_id)]}, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}}
    )
    if result.modified_count > 0:
        await invalidate_user_cache(user_id)
        return True
    return False
