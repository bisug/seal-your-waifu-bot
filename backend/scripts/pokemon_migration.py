"""One-shot pets → Pokémon data migration (Phase 5.2).

For every user doc that still carries pet fields:
1. $unset pets, current_pet, pet-related counters (starter_claimed is NOT
   touched — Pokémon starters use it too).
2. Gift a starter Pokémon to users who had a pet (they lose a companion,
   so they get one back): grants a random starter at level 5 and sets it
   active, only if they don't already own any Pokémon.
3. Drop the pet_catalog collection (code no longer references it).

Idempotent: safe to re-run. Run from backend/:
`uv run python scripts/pokemon_migration.py`
"""
import asyncio
import random
import sys

sys.path.insert(0, ".")

from backend.core.pokemon import STARTER_DEXES, grant_pokemon, set_active_pokemon  # noqa: E402


async def main() -> None:
    from backend.database import seal_db, user_collection

    await seal_db.ping()
    db = seal_db.db
    report: list[str] = []

    # 1. Strip pet fields from user docs.
    res = await user_collection.update_many(
        {
            "$or": [
                {"pets": {"$exists": True}},
                {"current_pet": {"$exists": True}},
                {"pet_count": {"$exists": True}},
                {"pet_xp": {"$exists": True}},
                {"pet_level": {"$exists": True}},
            ]
        },
        {"$unset": {
            "pets": "", "current_pet": "", "pet_count": "",
            "pet_xp": "", "pet_level": "",
        }},
    )
    report.append(f"user docs stripped of pet fields: {res.modified_count}")

    # 2. Gift a starter to users who had pets but own no Pokémon now.
    migrated = 0
    cursor = user_collection.find(
        {"pokemon": {"$exists": True, "$eq": []}}, {"id": 1}
    )
    async for doc in cursor:
        uid = doc["id"]
        dex = random.choice(STARTER_DEXES)
        if await grant_pokemon(uid, dex, level=5):
            await set_active_pokemon(uid, dex)
            migrated += 1
    report.append(f"starters gifted: {migrated}")

    # 3. Drop the pet catalog.
    names = await db.list_collection_names()
    if "pet_catalog" in names:
        await db["pet_catalog"].drop()
        report.append("dropped collection: pet_catalog")
    else:
        report.append("already absent: pet_catalog")

    for line in report:
        print(line)

    # Post-conditions
    leftover = await user_collection.count_documents({
        "$or": [
            {"pets": {"$exists": True}},
            {"current_pet": {"$exists": True}},
            {"pet_count": {"$exists": True}},
            {"pet_xp": {"$exists": True}},
            {"pet_level": {"$exists": True}},
        ]
    })
    assert leftover == 0, f"{leftover} user docs still carry pet fields"
    names_after = await db.list_collection_names()
    assert "pet_catalog" not in names_after
    print("POST-CONDITIONS OK")


if __name__ == "__main__":
    asyncio.run(main())
