"""Migration: copy user characters into a dedicated user_characters collection.

This is the DATA-ONLY first step of moving harems out of the user document.
It does NOT change any runtime code path — the embedded characters array
remains the source of truth until the application layer is migrated.

Each owned copy becomes one document:
    {user_id, char_id, name, anime, rarity, img_url, obtained_index}

Usage:
    python -m scripts.extract_characters --dry-run
    python -m scripts.extract_characters
"""
import argparse
import asyncio
import sys

from pymongo import AsyncMongoClient, InsertOne

from config import config

BATCH = 500


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    client = AsyncMongoClient(config.MONGO_URL, appname="seal-bot-migrate")
    db = client["Character_catchers"]
    users = db["user_collectionsss"]
    target = db["user_characters"]

    if not args.dry_run:
        await target.create_index([("user_id", 1), ("char_id", 1)])
        await target.create_index("char_id")

    seen_users = 0
    total_chars = 0
    ops = []
    async for user in users.find(
        {"characters": {"$exists": True, "$ne": []}},
        {"id": 1, "characters": 1},
    ):
        try:
            uid = int(user.get("id"))
        except (TypeError, ValueError):
            continue
        seen_users += 1
        for idx, char in enumerate(user.get("characters") or []):
            if not isinstance(char, dict) or char.get("id") is None:
                continue
            ops.append(InsertOne({
                "user_id": uid,
                "char_id": str(char.get("id")),
                "name": char.get("name"),
                "anime": char.get("anime"),
                "rarity": char.get("rarity"),
                "img_url": char.get("img_url"),
                "obtained_index": idx,
            }))
            total_chars += 1
            if len(ops) >= BATCH:
                if not args.dry_run:
                    await target.bulk_write(ops, ordered=False)
                ops = []
    if ops and not args.dry_run:
        await target.bulk_write(ops, ordered=False)

    verb = "would be extracted" if args.dry_run else "extracted"
    print(f"{total_chars} character copy(ies) across {seen_users} user(s) {verb}.")
    await client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)