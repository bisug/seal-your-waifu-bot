"""One-time migration: rebalance overvalued shop prices.

The 2026-09-01 rebalance cut top-tier Zenith prices by ~25x (e.g. Astral
2500 -> 100, Celestial 1000 -> 80) so the ladder tracks actual rarity and
caps at ~3 months of grinding. Defaults only seed a fresh `rarities`
collection; this script updates existing docs in place.

Only touches docs whose current shop_price differs from the target —
admin-tuned prices that already match are left alone, and re-running is
a no-op.

Usage:
    python -m scripts.rebalance_shop_prices --dry-run   # report only
    python -m scripts.rebalance_shop_prices             # apply
"""
import argparse
import asyncio

from pymongo import AsyncMongoClient

from config import config

# rarity_id -> target shop_price (must mirror core/rarities.py defaults).
TARGET_PRICES = {
    1: 1, 2: 2, 3: 4, 4: 6, 5: 10, 6: 30, 7: 45, 8: 60, 9: 60,
    10: 80, 11: 80, 12: 100, 13: 15, 14: 15, 15: 25, 16: 25,
    17: 20, 18: 12, 19: 3, 20: 10, 21: 35, 22: 45, 23: 60,
    24: 80, 25: 100,
}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args()

    client = AsyncMongoClient(
        config.MONGO_URL,
        appname="seal-bot-migrate",
        connectTimeoutMS=10_000,
        serverSelectionTimeoutMS=10_000,
    )
    db = client["Character_catchers"]
    rarities = db["rarities"]

    changed = 0
    async for doc in rarities.find({}):
        rid = doc["_id"]
        if not isinstance(rid, int) or rid not in TARGET_PRICES:
            continue
        current = int(doc.get("shop_price", 0) or 0)
        target = TARGET_PRICES[rid]
        if current == target:
            continue
        label = f"{doc.get('emoji', '')} {doc.get('name', '')}".strip()
        print(f"[{rid}] {label}: {current} -> {target} Zenith")
        changed += 1
        if not args.dry_run:
            await rarities.update_one({"_id": rid}, {"$set": {"shop_price": target}})

    verb = "would update" if args.dry_run else "updated"
    print(f"\n{changed} rarity doc(s) {verb}.")
    if changed and args.dry_run:
        print("Re-run without --dry-run to apply.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
