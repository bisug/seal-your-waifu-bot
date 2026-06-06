import asyncio

from Grabber.core.pets import ensure_user_pet_state, seed_pet_catalog
from Grabber.core.user import get_user_filter
from Grabber.core.utils import normalize_user_id
from Grabber.database import close_connections, user_collection


async def main() -> None:
    try:
        await seed_pet_catalog()

        processed = 0
        migrated = 0
        cursor = user_collection.find(
            {"pets": {"$exists": True}},
            {"id": 1, "pets": 1, "current_pet": 1},
        )

        async for user in cursor:
            user_id = user.get("id")
            if user_id is None:
                continue

            before_pets = user.get("pets")
            before_current_pet = user.get("current_pet")
            await ensure_user_pet_state(normalize_user_id(user_id), user)
            refreshed = await user_collection.find_one(
                get_user_filter(user_id),
                {"pets": 1, "current_pet": 1},
            )

            processed += 1
            if refreshed and (
                refreshed.get("pets") != before_pets
                or refreshed.get("current_pet") != before_current_pet
            ):
                migrated += 1

        print(f"Processed {processed} users; migrated {migrated} pet records.")
    finally:
        await close_connections()


if __name__ == "__main__":
    asyncio.run(main())
