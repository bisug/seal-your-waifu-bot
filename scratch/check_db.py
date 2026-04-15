import asyncio
import json
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Search for .env or use a default
load_dotenv()
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

async def test():
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    col = db['collection']
    doc = await col.find_one()
    print("--- Collection Sample ---")
    print(json.dumps(doc, default=str, indent=2))
    
    q_col = db['quiz_questions_collection']
    q_doc = await q_col.find_one()
    print("\n--- Quiz Sample ---")
    print(json.dumps(q_doc, default=str, indent=2))
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())
