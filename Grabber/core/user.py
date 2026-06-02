import asyncio
from typing import Any, Optional, Tuple
from Grabber import LOGGER
from Grabber.core.cache import (get_cached_user, get_total_ranked_users,
                                get_user_rank, invalidate_user_cache,
                                rebuild_leaderboard, rget, rset,
                                set_cached_user, update_user_rank)
from Grabber.core.tasks import run_background_task
from Grabber.database import user_collection


def _top_level_updated_fields(update_query: dict) -> set[str]:
    """Return top-level fields updated by operators other than $setOnInsert."""
    fields: set[str] = set()
    for operator, changes in update_query.items():
        if operator == "$setOnInsert" or not isinstance(changes, dict):
            continue
        for field in changes:
            fields.add(str(field).split(".", 1)[0])
    return fields


def get_user_id(user_id: Any) -> int:
    """Returns the user ID as a concrete integer."""
    try:
        if isinstance(user_id, list) and user_id:
            user_id = user_id[0]
        return int(user_id)
    except (ValueError, TypeError):
        return 0


def build_user_set_on_insert(
    user_id: Any,
    *,
    first_name: str | None = None,
    username: str | None = None,
) -> dict:
    """Build canonical fields for newly-created user documents."""
    uid = get_user_id(user_id)
    if uid <= 0:
        raise ValueError(f"Invalid Telegram user id: {user_id!r}")

    data = {
        "id": uid,
        "first_name": first_name or "User",
        "balance": 0,
        "zenith": 0,
        "char_count": 0,
        "xp": 0,
        "pass_type": "free",
        "claimed_levels": [],
        "season": 1,
    }
    if username:
        data["username"] = username
    return data


def add_user_set_on_insert(
    update_query: dict,
    user_id: Any,
    *,
    first_name: str | None = None,
    username: str | None = None,
) -> dict:
    """
    Merge canonical insert fields into a MongoDB update without conflicting with
    fields already touched by $set, $inc, $push, or other update operators.
    """
    defaults = build_user_set_on_insert(
        user_id,
        first_name=first_name,
        username=username,
    )
    for field in _top_level_updated_fields(update_query):
        defaults.pop(field, None)

    existing = update_query.setdefault("$setOnInsert", {})
    defaults.update(existing)
    existing.clear()
    existing.update(defaults)
    return update_query


async def ensure_user_document(
    user_id: Any,
    *,
    first_name: str | None = None,
    username: str | None = None,
) -> None:
    """Create the canonical user document if it does not exist, and refresh profile fields."""
    updates: dict = {}
    profile_updates = {}
    if first_name:
        profile_updates["first_name"] = first_name
    if username:
        profile_updates["username"] = username
    if profile_updates:
        updates["$set"] = profile_updates
    add_user_set_on_insert(updates, user_id, first_name=first_name, username=username)
    await user_collection.update_one(get_user_filter(user_id), updates, upsert=True)
    await invalidate_user_cache(get_user_id(user_id))


def get_user_filter(user_id: Any) -> dict:
    """Returns a MongoDB filter for both integer and string IDs."""
    uid = get_user_id(user_id)
    return {"id": {"$in": [uid, str(uid)]}}
async def get_user_data(user_id: int) -> Optional[dict]:
    """Fetch user data with Redis cache fallback."""
    cached = await get_cached_user(user_id)
    if cached is not None:
        return cached
    user = await user_collection.find_one(get_user_filter(user_id))
    if user:
        await set_cached_user(user_id, user)
    return user
async def update_user(user_id: int, update_query: dict):
    """Apply MongoDB update and invalidate cache. Increments version for OCC."""
    if "$inc" not in update_query:
        update_query["$inc"] = {}
    update_query["$inc"]["version"] = 1
    add_user_set_on_insert(update_query, user_id)
    await user_collection.update_one(get_user_filter(user_id), update_query, upsert=True)
    await invalidate_user_cache(user_id)
async def get_user_rank_with_fallback(user_id: int, user_xp: int) -> Tuple[int, int, float]:
    """
    Resolve a user's rank and total user count.
    Checks Redis ZSET first; falls back to a MongoDB count query.
    Schedules a full leaderboard rebuild if the ZSET is empty.
    Returns (rank, total_users, percentile).
    """
    total_users_str = await rget("total_app_users")
    if total_users_str:
        total_users = int(total_users_str)
    else:
        total_users = await user_collection.estimated_document_count()
        await rset("total_app_users", str(total_users), 3600)

    rank = await get_user_rank(user_id)
    if rank is None:
        LOGGER.info(f"Leaderboard ZSET miss for user {user_id}, falling back to Mongo count.")
        rank = await user_collection.count_documents({"xp": {"$gt": user_xp}}) + 1
        await update_user_rank(user_id, user_xp)
        if total_users > 0 and (await get_total_ranked_users()) == 0:
            run_background_task(rebuild_leaderboard(user_collection))

    percentile = round((1 - (rank / max(total_users, 1))) * 100, 1)
    return rank, total_users, percentile

async def add_char_to_user(user_id: int, character: dict):
    """Add a character to user collection and invalidate cache."""
    # Safety Check: Prevent string IDs from corrupting the DB
    if not isinstance(character, dict) or 'id' not in character:
        LOGGER.error(f"Attempted to insert invalid character into {user_id}'s harem: {character}")
        # Default placeholder to prevent catastrophic failures if it ever reaches here
        if isinstance(character, str):
            LOGGER.error("String passed instead of dict. Operation aborted to save DB integrity.")
            return
    await user_collection.update_one(
        get_user_filter(user_id),
        add_user_set_on_insert({
            "$push": {"characters": character}, 
            "$inc": {"char_count": 1, "version": 1},
        }, user_id),
        upsert=True
    )
    # Sync with Redis Harem Leaderboard
    user_doc = await user_collection.find_one(get_user_filter(user_id), {"char_count": 1})
    new_count = user_doc["char_count"] if user_doc else 1
    await update_user_rank(user_id, new_count, metric="harem")
    await invalidate_user_cache(user_id)
async def remove_char_from_user(user_id: int, char_id: str) -> bool:
    """
    Remove EXACTLY ONE instance of a character by ID.
    Uses versioning to prevent concurrent modification issues.
    """
    max_retries = 3
    for _ in range(max_retries):
        user = await user_collection.find_one(get_user_filter(user_id))
        if not user or 'characters' not in user:
            return False

        chars = user['characters']
        version = user.get('version', 0)

        # Find the first index of the character
        idx_to_remove = -1
        for i, c in enumerate(chars):
            if str(c.get('id')) == str(char_id):
                idx_to_remove = i
                break

        if idx_to_remove == -1:
            return False

        # Create new character list without that ONE specific instance
        new_chars = chars[:idx_to_remove] + chars[idx_to_remove+1:]

        # Atomic update with version check
        filt = get_user_filter(user_id)
        filt["version"] = version

        res = await user_collection.update_one(
            filt,
            {
                "$set": {"characters": new_chars},
                "$inc": {"char_count": -1, "version": 1}
            }
        )

        if res.modified_count > 0:
            await update_user_rank(user_id, len(new_chars), metric="harem")
            await invalidate_user_cache(user_id)
            return True

        # If we failed, someone else updated the user. Loop and retry.
        await asyncio.sleep(0.1)

    return False
async def get_active_pet(user_id: int) -> dict:
    """Retrieve currently active pet data."""
    from Grabber.core.pets import ensure_user_pet_state, find_pet, normalize_pet

    user = await ensure_user_pet_state(user_id)
    if not user or "current_pet" not in user:
        return None
    current_pet_ref = user["current_pet"]
    pets = [normalize_pet(p) for p in user.get("pets", [])]
    return find_pet(pets, current_pet_ref)
async def add_pet_xp(user_id: int, pet_ref: str, xp_amount: int):
    """Adds XP to pet and handles level-ups."""
    from Grabber.core.pets import ensure_user_pet_state, find_pet_index, get_pet_key, normalize_pet

    max_retries = 3
    for _ in range(max_retries):
        user = await ensure_user_pet_state(user_id)
        if not user:
            return
        pets = [normalize_pet(p) for p in user.get("pets", [])]
        pet_index = find_pet_index(pets, pet_ref)
        if pet_index == -1:
            return

        pet = pets[pet_index]
        level = pet.get("level", 1)
        xp = pet.get("xp", 0) + xp_amount
        xp_needed = level * 100
        original_level = level
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = level * 100

        luck = pet.get("luck", 0.1)
        if level > original_level:
            luck = round(luck + ((level - original_level) * 0.002), 3)

        filt = get_user_filter(user_id)
        if user.get("version") is None:
            filt["version"] = {"$exists": False}
        else:
            filt["version"] = user.get("version")
        result = await user_collection.update_one(
            filt,
            {
                "$set": {
                    f"pets.{pet_index}.id": get_pet_key(pet),
                    f"pets.{pet_index}.xp": xp,
                    f"pets.{pet_index}.level": level,
                    f"pets.{pet_index}.luck": luck,
                },
                "$inc": {"version": 1},
            },
        )
        if result.modified_count:
            await invalidate_user_cache(user_id)
            return
        await asyncio.sleep(0.05)
