import asyncio
import os
import sys

# Add the project root to sys.path so we can import Grabber modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Grabber.database import user_collection
from Grabber import LOGGER
import logging

# Configure logging for the script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MigrationV2")

async def migrate_users():
    """
    Migration Script v2:
    - Normalizes 'id' to int.
    - Populates 'char_count' from len(characters).
    """
    logger.info("Starting Seal-Bot-V2 Data Migration...")
    
    cursor = user_collection.find({})
    total_users = await user_collection.count_documents({})
    logger.info(f"Found {total_users} users to process.")
    
    processed = 0
    updated = 0
    errors = 0
    
    async for user in cursor:
        processed += 1
        user_id = user.get("id")
        
        # 1. Normalize ID to int if it's a string
        target_id = user_id
        if isinstance(user_id, str):
            try:
                target_id = int(user_id)
            except ValueError:
                logger.warning(f"Could not convert ID '{user_id}' to int. Skipping.")
                continue

        # 2. Calculate char_count
        char_list = user.get("characters") or []
        real_count = len(char_list)
        
        # 3. Determine if update is needed
        # Update if ID is string OR char_count is missing OR char_count is wrong
        needs_update = False
        update_query = {}
        
        if isinstance(user_id, str):
            needs_update = True
            update_query["id"] = target_id
            
        if user.get("char_count") != real_count:
            needs_update = True
            update_query["char_count"] = real_count
            
        if needs_update:
            try:
                # IMPORTANT: Use the original _id to target the document
                await user_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": update_query}
                )
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update user {user_id}: {e}")
                errors += 1
        
        if processed % 100 == 0:
            logger.info(f"Progress: {processed}/{total_users} (Updated: {updated}, Errors: {errors})")

    logger.info("Migration Complete!")
    logger.info(f"Summary: Total {processed}, Updated {updated}, Errors {errors}")

if __name__ == "__main__":
    asyncio.run(migrate_users())
