from typing import Optional
from backend.core.cache import (get_cached_balance, invalidate_user_cache,
                                set_cached_balance)
from backend.core.user import add_user_set_on_insert, get_user_filter
from backend.database import user_collection
async def get_user_balance(user_id: int) -> int:
    """
    Fetch the current shard balance for a user.
    Checks Redis cache first; falls back to MongoDB.
    """
    cached = await get_cached_balance(user_id)
    if cached is not None:
        return cached
    user = await user_collection.find_one(get_user_filter(user_id), {"balance": 1})
    balance = user.get("balance", 0) if user else 0
    await set_cached_balance(user_id, balance)
    return balance
async def update_user_balance(user_id: int, amount: int):
    """
    Increment or decrement a user's balance, then invalidate cache.
    """
    await user_collection.update_one(
        get_user_filter(user_id),
        add_user_set_on_insert({"$inc": {"balance": amount}}, user_id),
        upsert=True
    )
    await invalidate_user_cache(user_id)
async def check_and_deduct(user_id: int, amount: int) -> bool:
    """
    Atomically check balance and deduct. Invalidates cache on success.
    Returns True if successful, False otherwise.
    """
    result = await user_collection.update_one(
        {**get_user_filter(user_id), "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}}
    )
    if result.modified_count > 0:
        await invalidate_user_cache(user_id)
        return True
    return False
