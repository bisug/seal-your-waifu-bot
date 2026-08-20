"""One-time migration: add a stored `numeric_id` int field to anime characters.

The WebApp gallery's numeric sort previously recomputed a $regexMatch +
$convert aggregation over the whole collection on every paginated request.
This script stores the parsed integer once, so the sort can use a plain
indexed field.

Usage:
    python -m scripts.add_numeric_id --dry-run   # report only
    python -m scripts.add_numeric_id             # apply
"""
import argparse
import asyncio
import sys

from pymongo import AsyncMongoClient, UpdateOne

from config import config

BATCH = 500


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    client = AsyncMongoClient(config.MONGO_URL, appname="seal-bot-migrate")
    db = client["Character_catchers"]
    characters = db["anime_characterss"]

    if not args.dry_run:
        await characters.create_index("numeric_id", sparse=True)

    # Only touch docs missing the field or with a stale/null value.
    cursor = characters.find(
        {"$or": [{"numeric_id": {"$exists": False}}, {"numeric_id": None}]},
        {"id": 1},
    )

    ops = []
    fixed = 0
    skipped = 0
    async for doc in cursor:
        raw = doc.get("id")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            skipped += 1
            continue
        if not args.dry_run:
            ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"numeric_id": value}}))
            if len(ops) >= BATCH:
                await characters.bulk_write(ops, ordered=False)
                ops = []
        fixed += 1

    if ops and not args.dry_run:
        await characters.bulk_write(ops, ordered=False)

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"[{mode}] numeric_id set on {fixed} character(s), {skipped} non-numeric id(s) skipped.")
    await client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
