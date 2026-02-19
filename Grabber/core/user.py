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
                                                        
    res = await user_collection.update_one(
        {"id": user_id, "characters.id": char_id},
        {"$pull": {"characters": {"id": char_id}}}
    )
    return res.modified_count > 0

async def get_active_pet(user_id: int) -> dict:
                                                  
    user = await user_collection.find_one({"id": user_id})
    if not user or "current_pet" not in user:
        return None
    
    current_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    return next((p for p in pets if p["name"] == current_pet_name), None)

async def add_pet_xp(user_id: int, pet_name: str, xp_amount: int):
    """
    Adds XP to a pet atomically where possible.
    Note: Level-ups still require multi-step logic but we reduce the race window.
    """
    user = await user_collection.find_one({"id": user_id, "pets.name": pet_name})
    if not user:
        return

    # 1. Atomic XP increment
    await user_collection.update_one(
        {"id": user_id, "pets.name": pet_name},
        {"$inc": {"pets.$.xp": xp_amount}}
    )

    # 2. Re-fetch to check for level up
    user = await user_collection.find_one({"id": user_id, "pets.name": pet_name})
    pet = next((p for p in user['pets'] if p['name'] == pet_name), None)
    
    if pet:
        level = pet.get("level", 1)
        xp = pet.get("xp", 0)
        xp_needed = level * 100
        
        if xp >= xp_needed:
            # Level Up!
            new_xp = xp - xp_needed
            new_level = level + 1
            new_luck = round(pet.get("luck", 0.1) + 0.002, 3)
            
            await user_collection.update_one(
                {"id": user_id, "pets.name": pet_name},
                {
                    "$set": {
                        "pets.$.xp": new_xp,
                        "pets.$.level": new_level,
                        "pets.$.luck": new_luck
                    }
                }
            )
