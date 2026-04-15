import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client['Seal-Bot-V2']
    doc = await db.collection.find_one({}, {"rarity": 1})
    print(f"Rarity in DB: {doc.get('rarity')}")
    client.close()

if __name__ == "__main__":
    asyncio.run(check_db())
