from typing import Optional, Dict, Any
from Grabber.database import spawns_collection, message_counts_collection, user_totals_collection

async def get_chat_state(chat_id: int) -> Dict[str, Any]:
    """Fetch the current state for a chat from MongoDB."""
    state = await spawns_collection.find_one({"chat_id": chat_id})
    return state or {}

async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
    """Save an active spawn to MongoDB."""
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "last_character": character,
                "message_id": message_id,
                "first_correct_guess": None
            }
        },
        upsert=True
    )

async def clear_active_spawn(chat_id: int, user_id: int):
    """Mark a spawn as caught and clear the session data."""
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {"first_correct_guess": user_id},
            "$unset": {"last_character": "", "message_id": ""}
        }
    )

async def get_message_count(chat_id: int) -> int:
    doc = await message_counts_collection.find_one({"chat_id": str(chat_id)})
    return doc["count"] if doc else 0

async def increment_message_count(chat_id: int) -> int:
    """Atomic increment of message count in MongoDB."""
    res = await message_counts_collection.find_one_and_update(
        {"chat_id": str(chat_id)},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )
    return res["count"]

async def get_spawn_order(chat_id: int) -> int:
    state = await get_chat_state(chat_id)
    return state.get("spawn_order", 0)

async def increment_spawn_order(chat_id: int):
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {"$inc": {"spawn_order": 1}},
        upsert=True
    )

async def get_chat_frequency(chat_id: int) -> int:
    doc = await user_totals_collection.find_one(
        {"chat_id": str(chat_id)},
        projection={"message_frequency": 1}
    )
    return doc.get("message_frequency", 100) if doc else 100
