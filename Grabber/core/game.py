from Grabber.database import user_collection
from typing import Optional

async def get_user_balance(user_id: int) -> int:
    user = await user_collection.find_one({"id": user_id}, {"balance": 1})
    return user.get("balance", 0) if user else 0

async def update_user_balance(user_id: int, amount: int):
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

async def check_and_deduct(user_id: int, amount: int) -> bool:
                                             
    result = await user_collection.update_one(
        {"id": user_id, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}}
    )
    return result.modified_count > 0
