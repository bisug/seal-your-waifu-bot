"""One-time migration: consolidate and rename rarities (2026-09-01).

Removes 3 redundant tiers by reassigning their characters and harem
entries to the nearest surviving sibling, and applies 2 renames. The
retired rarity docs are deleted from the `rarities` collection; new
default tiers (Radiant/Eclipse/Seraph) are backfilled by load_rarities()
on next startup.

Merges (old label -> new label):
    💎 Antique      -> 💎 Mythical
    💸 Luxury       -> 💮 Exclusive
    🎏 Limited      -> 🔮 Limited Edition

Renames (label change only, same rarity_id):
    🎞️ AMV   -> 🎞️ Cinematic
    🔮 Mystic -> 🌀 Arcane

Idempotent: re-running is a no-op (updates match nothing once applied).

Usage:
    python -m scripts.merge_rarity --dry-run   # report only
    python -m scripts.merge_rarity             # apply
"""
import argparse
import asyncio

from pymongo import AsyncMongoClient

from config import config

# old composed label -> (new composed label, new rarity_id)
MERGES = {
    "💎 Antique": ("💎 Mythical", 23),
    "💸 Luxury": ("💮 Exclusive", 6),
    "🎏 Limited": ("🔮 Limited Edition", 7),
}

# rarity_id -> (old label, new label)
RENAMES = {
    11: ("🎞️ AMV", "🎞️ Cinematic"),
    22: ("🔮 Mystic", "🌀 Arcane"),
}

DB_NAME = "Character_catchers"
CHARACTERS = "anime_characterss"
USERS = "user_collectionsss"
RARITIES = "rarities"


async def count(client, coll, filt) -> int:
    return await client[DB_NAME][coll].count_documents(filt)


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
    db = client[DB_NAME]
    characters = db[CHARACTERS]
    users = db[USERS]
    rarities = db[RARITIES]

    # 1. Merges: reassign character docs and harem entries.
    for old_label, (new_label, new_rid) in MERGES.items():
        char_count = await count(client, CHARACTERS, {"rarity": old_label})
        harem_count = await count(client, USERS, {"characters.rarity": old_label})
        print(f"merge {old_label} -> {new_label}: {char_count} char doc(s), {harem_count} user(s) with harem entries")
        if args.dry_run or not (char_count or harem_count):
            continue
        await characters.update_many(
            {"rarity": old_label},
            {"$set": {"rarity": new_label, "rarity_id": new_rid}},
        )
        await users.update_many(
            {"characters.rarity": old_label},
            {"$set": {"characters.$[c].rarity": new_label, "characters.$[c].rarity_id": new_rid}},
            array_filters=[{"c.rarity": old_label}],
        )

    # 2. Renames: same treatment via the canonical label propagation.
    for rid, (old_label, new_label) in RENAMES.items():
        char_count = await count(client, CHARACTERS, {"rarity": old_label})
        harem_count = await count(client, USERS, {"characters.rarity": old_label})
        print(f"rename {old_label} -> {new_label} (id {rid}): {char_count} char doc(s), {harem_count} user(s)")
        if args.dry_run or not (char_count or harem_count):
            continue
        await rarities.update_one({"_id": rid}, {"$set": {"emoji": new_label.split(" ", 1)[0], "name": new_label.split(" ", 1)[1]}})
        await characters.update_many({"rarity": old_label}, {"$set": {"rarity": new_label, "rarity_id": rid}})
        await users.update_many(
            {"characters.rarity": old_label},
            {"$set": {"characters.$[c].rarity": new_label, "characters.$[c].rarity_id": rid}},
            array_filters=[{"c.rarity": old_label}],
        )

    # 3. Delete the retired rarity docs (merge sources only).
    retired_ids = [9, 17, 18]
    if not args.dry_run:
        result = await rarities.delete_many({"_id": {"$in": retired_ids}})
        print(f"deleted {result.deleted_count} retired rarity doc(s): {retired_ids}")
    else:
        existing = await count(client, RARITIES, {"_id": {"$in": retired_ids}})
        print(f"would delete {existing} retired rarity doc(s): {retired_ids}")

    if args.dry_run:
        print("\nDry run — re-run without --dry-run to apply.")
    else:
        print("\nDone. Restart the bot (or /rarityrefresh) to reload live dicts;")
        print("load_rarities() will backfill the new Radiant/Eclipse/Seraph tiers.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
