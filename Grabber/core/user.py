from Grabber.database import user_collection

async def get_user_data(user_id: int) -> dict or None:
    return await user_collection.find_one({"id": user_id})

async def update_user(user_id: int, update_query: dict):
    await user_collection.update_one({"id": user_id}, update_query, upsert=True)

async def add_char_to_user(user_id: int, character: dict):
    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": character}},
        upsert=True
    )

async def remove_char_from_user(user_id: int, char_id: str) -> bool:
    """Atomic removal of a single character instance."""
    res = await user_collection.update_one(
        {"id": user_id, "characters.id": char_id},
        {"$pull": {"characters": {"id": char_id}}}
    )
    return res.modified_count > 0

async def get_active_pet(user_id: int) -> dict:
    """Get the currently active pet for a user."""
    user = await user_collection.find_one({"id": user_id})
    if not user or "current_pet" not in user:
        return None
    
    current_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    return next((p for p in pets if p["name"] == current_pet_name), None)

async def add_pet_xp(user_id: int, pet_name: str, xp_amount: int):
    """Add XP to a specific pet and level up if necessary."""
    user = await user_collection.find_one({"id": user_id})
    if not user:
        return

    pets = user.get("pets", [])
    for pet in pets:
        if pet["name"] == pet_name:
            xp = pet.get("xp", 0) + xp_amount
            level = pet.get("level", 1)
            
            # Simple level up logic: level * 100 XP required
            xp_needed = level * 100
            if xp >= xp_needed:
                xp -= xp_needed
                level += 1
                # Level up bonus: +0.2% luck per level
                pet["luck"] = round(pet.get("luck", 0.1) + 0.002, 3)
            
            pet["xp"] = xp
            pet["level"] = level
            break
    
    await user_collection.update_one({"id": user_id}, {"$set": {"pets": pets}})
