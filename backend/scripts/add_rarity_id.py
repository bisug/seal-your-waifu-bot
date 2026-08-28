"""One-time migration: backfill `rarity_id` on characters and user harems.

The rarity table (db.rarities, _id = rarity_id) is the single source of
truth for rarity emoji/name. This script adds the numeric `rarity_id`
next to every stored display label so renames can propagate by id.

Idempotent: only touches docs/entries missing the field.

Usage:
    python -m scripts.add_rarity_id --dry-run   # report only
    python -m scripts.add_rarity_id             # apply
"""
import argparse
import asyncio

from pymongo import AsyncMongoClient

from config import config


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    client = AsyncMongoClient(config.MONGO_URL, appname="seal-bot-migrate")
    db = client["Character_catchers"]
    characters = db["anime_characterss"]
    users = db["user_collectionsss"]
    rarities = db["rarities"]

    # Build label -> rarity_id from the rarity table.
    label_to_id: dict[str, int] = {}
    async for doc in rarities.find({}):
        if isinstance(doc["_id"], int):
            emoji, name = doc.get("emoji", ""), doc.get("name", "")
            label_to_id[f"{emoji} {name}".strip()] = doc["_id"]
    if not label_to_id:
        print("rarities collection is empty — run the bot once to seed it, then retry.")
        return

    if not args.dry_run:
        await characters.create_index("rarity_id", sparse=True)

    # 1. Character docs: one update_many per rarity label.
    char_total = 0
    for label, rid in label_to_id.items():
        filt = {"rarity": label, "rarity_id": {"$exists": False}}
        if args.dry_run:
            n = await characters.count_documents(filt)
        else:
            result = await characters.update_many(filt, {"$set": {"rarity_id": rid}})
            n = result.modified_count
        if n:
            print(f"characters [{label} -> {rid}]: {n}")
            char_total += n
    print(f"characters total: {char_total}")

    # 2. User harem entries: one array-filtered update_many per rarity label.
    user_total = 0
    for label, rid in label_to_id.items():
        filt = {"characters.rarity": label}
        update = {"$set": {"characters.$[c].rarity_id": rid}}
        array_filters = [{"c.rarity": label, "c.rarity_id": {"$exists": False}}]
        if args.dry_run:
            n = await users.count_documents(filt)
        else:
            result = await users.update_many(filt, update, array_filters=array_filters)
            n = result.modified_count
        if n:
            print(f"users [{label} -> {rid}]: {n} user docs")
            user_total += n
    print(f"user docs touched total: {user_total}")

    await client.close()
    print("done." if not args.dry_run else "dry run complete — nothing written.")


if __name__ == "__main__":
    asyncio.run(main())
