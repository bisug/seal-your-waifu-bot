import asyncio
from Grabber import collection

async def main():
    char = await collection.find_one()
    if char:
        print(f"Name: {char.get('name')}")
        print(f"Rarity: {char.get('rarity')}")
    else:
        print("No characters found")

if __name__ == "__main__":
    asyncio.run(main())
