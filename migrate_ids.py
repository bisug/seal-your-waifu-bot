import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def migrate():
    """
    Utility script to find all users in the database where 'id' is a string,
    and convert them definitively to integers to standardize indexing.
    """
    print("Connecting to MongoDB...")
    try:
        client = AsyncIOMotorClient(config.MONGO_URL)
        # Using the exact same DB and collection names from Grabber/database/__init__.py
        db = client['Character_catchers']
        users = db["user_collectionsss"]
    except Exception as e:
        print(f"Failed to connect to Mongo: {e}")
        return
        
    print("Finding users with string IDs...")
    # Find users where id type is string
    cursor = users.find({"id": {"$type": "string"}})
    
    migrated_count = 0
    error_count = 0
    
    async for user in cursor:
        try:
            old_id = user["id"]
            new_id = int(old_id)
            
            # Update the document to cast id to integer
            await users.update_one(
                {"_id": user["_id"]},
                {"$set": {"id": new_id}}
            )
            migrated_count += 1
            if migrated_count % 100 == 0:
                print(f"Migrated {migrated_count} users...")
                
        except ValueError:
            print(f"Warning: Could not parse ID '{old_id}' to int for document {user['_id']}")
            error_count += 1
            
    print(f"\nMigration complete!")
    print(f"Successfully converted {migrated_count} string IDs to integer.")
    if error_count > 0:
        print(f"Warning: {error_count} parsing errors occurred. Some IDs could not be formatted as ints.")

if __name__ == "__main__":
    asyncio.run(migrate())
