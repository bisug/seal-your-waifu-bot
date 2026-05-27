import asyncio
import os
import sys

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import AsyncMongoClient
from config import config
DEST_MONGO_URL = config.MONGO_URL

SOURCE_MONGO_URL = "mongodb+srv://sumiloo:gurasnani@cluster0.nb0umdm.mongodb.net/?retryWrites=true&w=majority"
SOURCE_DB_NAME = "dear_waifu"
SOURCE_COLLECTION = "anime_characters"

# Target DB uses the same name in Seal-bot typically (or whatever is default)
# Seal-bot uses default database from connection string usually, but we can just use "Cluster0" or whatever motor defaults to
# Let's import the actual collection from Grabber.database to be perfectly safe
from Grabber.database import collection as dest_collection

RARITY_MAPPING = {
    "winter": "❄️ Winter",
    "summer": "☀️ Summer",
    "valentine": "💖 Valentine",
    "halloween": "🎃 Halloween",
    "common": "⚪ Common",
    "medium": "🟢 Medium",
    "rare": "🟠 Rare",
    "legendary": "🟡 Legendary",
    "cosmic": "💠 Cosmic",
    "exclusive": "💮 Exclusive",
    "limited edition": "🔮 Limited Edition",
    "royal": "🫧 Royal",
    "antique": "💎 Antique",
    "celestial": "🎐 Celestial",
    "amv": "🎞️ AMV",
    "prestige": "🪽 Prestige"
}

def map_rarity(raw_rarity):
    """Maps a raw rarity string from the old DB to the new format with emojis."""
    if not raw_rarity:
        return "⚪ Common"
    
    raw_lower = str(raw_rarity).lower()
    for key, mapped_val in RARITY_MAPPING.items():
        if key in raw_lower:
            return mapped_val
            
    # If no mapping found, return the original or default
    return raw_rarity

async def migrate():
    print(f"Connecting to source MongoDB...")
    source_client = AsyncMongoClient(SOURCE_MONGO_URL)
    source_db = source_client[SOURCE_DB_NAME]
    source_col = source_db[SOURCE_COLLECTION]
    
    total_docs = await source_col.count_documents({})
    print(f"Found {total_docs} characters to migrate.")
    
    if total_docs == 0:
        print("No characters found. Exiting.")
        return

    print(f"Connecting to destination MongoDB via Grabber...")
    # The dest_collection is already initialized via Grabber.database
    
    batch_size = 1000
    migrated_count = 0
    
    cursor = source_col.find({})
    batch = []
    
    async for doc in cursor:
        # Remove the old _id so we get new ones, or keep it if we want to retain IDs
        # It's usually safer to keep the ID unless there are conflicts, but anime characters in Seal-bot have 'id' field
        
        # Make sure rarity is mapped properly
        old_rarity = doc.get("rarity", "")
        new_rarity = map_rarity(old_rarity)
        
        doc["rarity"] = new_rarity
        
        # Check if character already exists by ID
        char_id = doc.get("id")
        if char_id:
            # We use replace_one with upsert=True to insert or update
            batch.append(
                dest_collection.replace_one({"id": char_id}, doc, upsert=True)
            )
        else:
            # If no custom 'id', just insert
            # Delete _id to prevent duplicate key errors if migrating to the same DB
            if "_id" in doc:
                del doc["_id"]
            batch.append(
                dest_collection.insert_one(doc)
            )
            
        if len(batch) >= batch_size:
            await asyncio.gather(*batch)
            migrated_count += len(batch)
            print(f"Migrated {migrated_count}/{total_docs} characters...")
            batch = []
            
    # Process remaining
    if batch:
        await asyncio.gather(*batch)
        migrated_count += len(batch)
        print(f"Migrated {migrated_count}/{total_docs} characters...")
        
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
