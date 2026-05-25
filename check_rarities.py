import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    mongo_url = "mongodb+srv://sumiloo:gurasnani@cluster0.nb0umdm.mongodb.net/?retryWrites=true&w=majority"
    client = AsyncIOMotorClient(mongo_url)
    db = client["dear_waifu"]
    collection = db["anime_characters"]
    
    count = await collection.count_documents({})
    print(f"Total characters: {count}")
    
    rarities = await collection.distinct("rarity")
    print(f"Distinct rarities: {rarities}")
    
    # get a sample document
    sample = await collection.find_one({})
    print(f"Sample doc: {sample}")

asyncio.run(main())
