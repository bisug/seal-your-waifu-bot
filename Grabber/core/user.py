from typing import Any, Optional
from Grabber.core.cache import (get_cached_user, invalidate_user_cache,
                                set_cached_user, update_user_rank)
from Grabber.database import user_collection
def get_user_id(user_id: Any) -> int:
    """Returns the user ID as a concrete integer."""
    try:
        if isinstance(user_id, list) and user_id:
            user_id = user_id[0]
        return int(user_id)
    except (ValueError, TypeError):
        return 0
def get_user_filter(user_id: Any) -> dict:
    """Returns a MongoDB filter for both integer and string IDs."""
    uid = get_user_id(user_id)
    return {"id": {"$in": [uid, str(uid)]}}
async def get_user_data(user_id: int) -> Optional[dict]:
    """Fetch user data with Redis cache fallback."""
    cached = await get_cached_user(user_id)
    if cached is not None:
        return cached
    user = await user_collection.find_one(get_user_filter(user_id))
    if user:
        await set_cached_user(user_id, user)
    return user
async def update_user(user_id: int, update_query: dict):
    """Apply MongoDB update and invalidate cache. Increments version for OCC."""
    if "$inc" not in update_query:
        update_query["$inc"] = {}
    update_query["$inc"]["version"] = 1
    await user_collection.update_one(get_user_filter(user_id), update_query, upsert=True)
    await invalidate_user_cache(user_id)
from Grabber import LOGGER
async def add_char_to_user(user_id: int, character: dict):
    """Add a character to user collection and invalidate cache."""
    # Safety Check: Prevent string IDs from corrupting the DB
    if not isinstance(character, dict) or 'id' not in character:
        LOGGER.error(f"Attempted to insert invalid character into {user_id}'s harem: {character}")
        # Default placeholder to prevent catastrophic failures if it ever reaches here
        if isinstance(character, str):
            LOGGER.error("String passed instead of dict. Operation aborted to save DB integrity.")
            return
    await user_collection.update_one(
        get_user_filter(user_id),
        {"$push": {"characters": character}, "$inc": {"char_count": 1, "version": 1}},
        upsert=True
    )
    # Sync with Redis Harem Leaderboard
    new_count = (await user_collection.find_one(get_user_filter(user_id), {"char_count": 1}))["char_count"]
    await update_user_rank(user_id, new_count, metric="harem")
    await invalidate_user_cache(user_id)
async def remove_char_from_user(user_id: int, char_id: str) -> bool:
    """Remove a character by ID and return success status."""
    filt = get_user_filter(user_id)
    filt["characters.id"] = char_id
    res = await user_collection.update_one(
        filt,
        {"$pull": {"characters": {"id": char_id}}, "$inc": {"char_count": -1, "version": 1}}
    )
    if res.modified_count > 0:
        new_count = (await user_collection.find_one({"id": get_user_id(user_id)}, {"char_count": 1}))["char_count"]
        await update_user_rank(user_id, new_count, metric="harem")
    return res.modified_count > 0
async def get_active_pet(user_id: int) -> dict:
    """Retrieve currently active pet data."""
    user = await user_collection.find_one(get_user_filter(user_id))
    if not user or "current_pet" not in user:
        return None
    current_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    return next((p for p in pets if p["name"] == current_pet_name), None)
async def add_pet_xp(user_id: int, pet_name: str, xp_amount: int):
    """Adds XP to pet and handles level-ups."""
    user = await user_collection.find_one_and_update(
        {**get_user_filter(user_id), "pets.name": pet_name},
        {"$inc": {"pets.$.xp": xp_amount}},
        return_document=True
    )
    if not user:
        return
    pet = next((p for p in user['pets'] if p['name'] == pet_name), None)
    if pet:
        level = pet.get("level", 1)
        xp = pet.get("xp", 0)
        xp_needed = level * 100
        original_level = level
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = level * 100
        if level > original_level:
            # Calculate luck increase based on levels gained
            luck_gain = (level - original_level) * 0.002
            new_luck = round(pet.get("luck", 0.1) + luck_gain, 3)
            await user_collection.update_one(
                {**get_user_filter(user_id), "pets.name": pet_name},
                {
                    "$set": {
                        "pets.$.xp": xp,
                        "pets.$.level": level,
                        "pets.$.luck": new_luck
                    }
                }
            )
            await invalidate_user_cache(user_id)
