from Grabber.database import user_collection
from Grabber.core.cache import invalidate_user_cache, get_cached_user, set_cached_user

async def get_user_data(user_id: int) -> dict or None:
    """
    Fetch all data associated with a user.
    Checks Redis first, then MongoDB.
    """
    cached = await get_cached_user(user_id)
    if cached is not None:
        return cached
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if user:
        await set_cached_user(user_id, user)
    return user

async def update_user(user_id: int, update_query: dict):
    """
    Apply a MongoDB update query to a user's document and invalidate cache.
    """
    await user_collection.update_one({"id": {"$in": [user_id, str(user_id)]}}, update_query, upsert=True)
    await invalidate_user_cache(user_id)

async def add_char_to_user(user_id: int, character: dict):
    """
    Add a character object to the user's collection and invalidate cache.
    """
    await user_collection.update_one(
        {"id": {"$in": [user_id, str(user_id)]}},
        {"$push": {"characters": character}},
        upsert=True
    )
    await invalidate_user_cache(user_id)

async def remove_char_from_user(user_id: int, char_id: str) -> bool:
    """
    Remove a character from the user's collection by its ID.
    Returns True if the character was found and removed.
    """
    res = await user_collection.update_one(
        {"id": {"$in": [user_id, str(user_id)]}, "characters.id": char_id},
        {"$pull": {"characters": {"id": char_id}}}
    )
    return res.modified_count > 0

async def get_active_pet(user_id: int) -> dict:
    """
    Retrieve the data for the user's currently active pet.
    """
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user or "current_pet" not in user:
        return None

    current_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    return next((p for p in pets if p["name"] == current_pet_name), None)

async def add_pet_xp(user_id: int, pet_name: str, xp_amount: int):
    """
    Adds XP to a pet. Uses find_one_and_update with return_document=True
    to get the post-update state in a single round-trip and check for level-up
    without an extra re-fetch.
    """
    user = await user_collection.find_one_and_update(
        {"id": {"$in": [user_id, str(user_id)]}, "pets.name": pet_name},
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

        if xp >= xp_needed:
            new_xp = xp - xp_needed
            new_level = level + 1
            new_luck = round(pet.get("luck", 0.1) + 0.002, 3)

            await user_collection.update_one(
                {"id": {"$in": [user_id, str(user_id)]}, "pets.name": pet_name},
                {
                    "$set": {
                        "pets.$.xp": new_xp,
                        "pets.$.level": new_level,
                        "pets.$.luck": new_luck
                    }
                }
            )
