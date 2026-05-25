import asyncio
from pyrogram import filters, types
from pymongo import AsyncMongoClient

from Grabber import app, OWNER_ID, LOGGER
from Grabber.database import collection as dest_collection

SOURCE_MONGO_URL = "mongodb+srv://sumiloo:gurasnani@cluster0.nb0umdm.mongodb.net/?retryWrites=true&w=majority"
SOURCE_DB_NAME = "dear_waifu"
SOURCE_COLLECTION = "anime_characters"

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

@app.on_message(filters.command("migrate") & filters.user(OWNER_ID))
async def migrate_characters_cmd(client, message: types.Message):
    status_msg = await message.reply_text("Connecting to source MongoDB...")
    
    try:
        source_client = AsyncMongoClient(SOURCE_MONGO_URL)
        source_db = source_client[SOURCE_DB_NAME]
        source_col = source_db[SOURCE_COLLECTION]
        
        total_docs = await source_col.count_documents({})
        if total_docs == 0:
            await status_msg.edit_text("No characters found in the source database. Exiting.")
            return
            
        await status_msg.edit_text(f"Found {total_docs} characters to migrate. Starting migration...")
        
        batch_size = 1000
        migrated_count = 0
        
        cursor = source_col.find({})
        batch = []
        
        async for doc in cursor:
            # Map rarity
            old_rarity = doc.get("rarity", "")
            new_rarity = map_rarity(old_rarity)
            doc["rarity"] = new_rarity
            
            char_id = doc.get("id")
            if char_id:
                # Upsert by id
                batch.append(
                    dest_collection.replace_one({"id": char_id}, doc, upsert=True)
                )
            else:
                # Insert without _id to prevent duplicate key errors
                if "_id" in doc:
                    del doc["_id"]
                batch.append(
                    dest_collection.insert_one(doc)
                )
                
            if len(batch) >= batch_size:
                await asyncio.gather(*batch)
                migrated_count += len(batch)
                await status_msg.edit_text(f"Migrated {migrated_count}/{total_docs} characters...")
                batch = []
                
        # Process remaining
        if batch:
            await asyncio.gather(*batch)
            migrated_count += len(batch)
            
        await status_msg.edit_text(f"Migration complete! Successfully migrated {migrated_count}/{total_docs} characters.")
        
    except Exception as e:
        LOGGER.error(f"Error during migration: {e}")
        await status_msg.edit_text(f"An error occurred during migration: {str(e)}")
