from Grabber.database import user_collection
import asyncio

async def migrate():
    print("Starting char_count migration...")
    count = 0
    async for user in user_collection.find({"characters": {"$exists": True}}):
        char_count = len(user.get("characters", []))
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"char_count": char_count}}
        )
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} users...")
    print(f"Migration complete! Processed {count} users.")

if __name__ == "__main__":
    asyncio.run(migrate())
