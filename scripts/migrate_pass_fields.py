from Grabber.database import user_collection
import asyncio
from Grabber import LOGGER

async def migrate():
    LOGGER.info("Starting conversion of pass_claimed to claimed_levels...")
    
    # 1. Find all users with pass_claimed
    cursor = user_collection.find({"pass_claimed": {"$exists": True}})
    count = 0
    async for user in cursor:
        pass_claimed = user.get("pass_claimed")
        claimed_levels = user.get("claimed_levels")
        
        # Defensive handling for non-list types
        pass_claimed_list = pass_claimed if isinstance(pass_claimed, list) else []
        claimed_levels_list = claimed_levels if isinstance(claimed_levels, list) else []
        
        # Merge the lists without duplicates
        merged = list(set(pass_claimed_list + claimed_levels_list))
        
        await user_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"claimed_levels": merged},
                "$unset": {"pass_claimed": ""}
            }
        )
        count += 1
        
    LOGGER.info(f"Migration complete. Processed {count} users.")

if __name__ == "__main__":
    asyncio.run(migrate())
