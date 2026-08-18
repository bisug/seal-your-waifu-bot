"""One-time migration: normalize user IDs stored as strings to integers.

Legacy documents store Telegram user IDs inconsistently as int and str,
forcing every query to pay for {"id": {"$in": [uid, str(uid)]}}. This script
rewrites string IDs to ints so queries can use a plain indexed {"id": uid}.

Usage:
    python -m scripts.normalize_ids --dry-run   # report only
    python -m scripts.normalize_ids             # apply

After running, flush stale Redis caches:
    redis-cli --scan --pattern 'user:*'   | xargs -r redis-cli del
    redis-cli --scan --pattern 'balance:*'| xargs -r redis-cli del
"""
import argparse
import asyncio
import sys

from pymongo import AsyncMongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError

from config import config

BATCH = 500


async def normalize_field(collection, field: str, dry_run: bool) -> int:
    # Materialize first: _id fixes delete docs mid-iteration.
    docs = [doc async for doc in collection.find({field: {"$type": "string"}}, {field: 1})]
    ops = []
    fixed = 0
    for doc in docs:
        raw = doc.get(field)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            print(f"  ! skipping non-numeric {field}={raw!r} in {doc.get('_id')}")
            continue
        if field == "_id":
            # _id is immutable: re-insert the doc under the new _id, drop the old one.
            if not dry_run:
                full = await collection.find_one({"_id": doc["_id"]})
                if full is None:
                    continue
                full["_id"] = value
                try:
                    await collection.insert_one(full)
                except DuplicateKeyError:
                    print(f"  ! int _id {value} already exists, dropping string duplicate {doc['_id']!r}")
                await collection.delete_one({"_id": doc["_id"]})
        else:
            ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {field: value}}))
            if len(ops) >= BATCH and not dry_run:
                await collection.bulk_write(ops, ordered=False)
                ops = []
        fixed += 1
    if ops and not dry_run:
        await collection.bulk_write(ops, ordered=False)
    return fixed


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    client = AsyncMongoClient(config.MONGO_URL, appname="seal-bot-migrate")
    db = client["Character_catchers"]

    targets = [
        (db["user_collectionsss"], "id"),
        (db["group_user_totals"], "user_id"),
        (db["total_pm_users"], "_id"),
        (db["sudos"], "user_id"),
        (db["global_user_bans"], "user_id"),
        (db["global_group_bans"], "chat_id"),
        (db["star_orders"], "user_id"),
    ]

    mode = "DRY RUN" if args.dry_run else "APPLYING"
    print(f"ID normalization ({mode})")
    total = 0
    for collection, field in targets:
        n = await normalize_field(collection, field, args.dry_run)
        print(f"  {collection.name}.{field}: {n} doc(s)")
        total += n
    print(f"Total: {total} doc(s) {'would be' if args.dry_run else ''} normalized.")
    await client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)