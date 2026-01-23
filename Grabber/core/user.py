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
