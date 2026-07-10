import time
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple

from Grabber import LOGGER
from Grabber.database import user_collection, collection, r
from Grabber.core.utils import get_now_utc, get_user_id_query
from Grabber.core.cache import invalidate_user_cache
from Grabber.core.progression import add_xp

MAX_ENERGY = 5
RECHARGE_MINUTES = 20

async def get_user_energy(user_id: int, user_data: Optional[dict] = None) -> Tuple[int, Optional[datetime]]:
    """Calculates and updates user energy based on time elapsed."""
    if user_data is None:
        user_data = await user_collection.find_one(get_user_id_query(user_id))

    if not user_data:
        return MAX_ENERGY, None

    current_energy = user_data.get("energy", MAX_ENERGY)
    last_recharge = user_data.get("last_energy_recharge")
    now = get_now_utc()

    if current_energy >= MAX_ENERGY:
        return MAX_ENERGY, None

    if last_recharge is None:
        # Initialize if missing
        await user_collection.update_one(
            get_user_id_query(user_id),
            {"$set": {"energy": MAX_ENERGY, "last_energy_recharge": now}}
        )
        return MAX_ENERGY, None

    if isinstance(last_recharge, datetime):
        last_recharge_dt = last_recharge
    else:
        # Fallback for unexpected types
        last_recharge_dt = now

    diff = now - last_recharge_dt
    minutes_passed = diff.total_seconds() / 60
    energy_gained = int(minutes_passed // RECHARGE_MINUTES)

    if energy_gained > 0:
        new_energy = min(MAX_ENERGY, current_energy + energy_gained)
        # Advance last_recharge by the number of full recharge intervals consumed
        new_recharge_time = last_recharge_dt + timedelta(minutes=energy_gained * RECHARGE_MINUTES)

        if new_energy == MAX_ENERGY:
            new_recharge_time = now

        await user_collection.update_one(
            get_user_id_query(user_id),
            {"$set": {"energy": new_energy, "last_energy_recharge": new_recharge_time}}
        )
        await invalidate_user_cache(user_id)
        return new_energy, new_recharge_time

    return current_energy, last_recharge_dt

async def consume_energy(user_id: int, game_type: Optional[str] = None) -> bool:
    """Consumes 1 energy point if available. Optionally starts a session."""
    user_data = await user_collection.find_one(get_user_id_query(user_id))
    current_energy, last_recharge = await get_user_energy(user_id, user_data)

    if current_energy <= 0:
        return False

    now = get_now_utc()
    update_fields = {
        "$inc": {"energy": -1},
    }

    # If we were at max, set the recharge timer to now
    if current_energy == MAX_ENERGY:
        update_fields["$set"] = {"last_energy_recharge": now}

    await user_collection.update_one(get_user_id_query(user_id), update_fields)

    if game_type and r:
        # Store start time in Redis for anti-cheat
        session_key = f"minigame_session:{user_id}:{game_type}"
        await r.set(session_key, str(now.timestamp()), ex=300) # 5 min session

    await invalidate_user_cache(user_id)
    return True

async def validate_session(user_id: int, game_type: str) -> Optional[float]:
    """Returns elapsed time since game start, or None if no session."""
    if not r:
        return 10.0 # Fallback if no redis

    session_key = f"minigame_session:{user_id}:{game_type}"
    start_time_str = await r.get(session_key)
    if not start_time_str:
        return None

    await r.delete(session_key)
    start_time = float(start_time_str)
    return get_now_utc().timestamp() - start_time

async def reward_minigame(user_id: int, game_type: str, score: int = 0, time_taken: float = 0) -> Dict[str, Any]:
    """Calculates and applies rewards for mini-games."""

    # Basic rewards
    shards = 0
    xp = 0
    character_reward = None

    if game_type == "cipher_match":
        # Anti-cheat: 8 pairs matched in less than 3 seconds is highly suspicious
        if score >= 8 and time_taken < 3.0:
             LOGGER.warning(f"User {user_id} suspicious Cipher Match: {score} pairs in {time_taken}s")
             return {"error": "Suspicious activity detected"}

        # Score is pairs matched
        base_shards = score * 15
        shards = base_shards + random.randint(0, 50)
        xp = score * 3 + random.randint(0, 10)

        # Bonus for speed
        if time_taken < 15:
            shards += 50
            xp += 20

    elif game_type == "nexus_wheel":
        # Random spin result
        roll = random.random()
        if roll < 0.03: # 3% chance for a character (slightly balanced)
            character_reward = await get_random_character(["⚪ Common", "🟢 Medium"])
            shards = 50
            xp = 10
        elif roll < 0.10: # 7% chance for EPIC shards
            shards = random.randint(1000, 2000)
            xp = 100
        elif roll < 0.30: # 20% chance for decent shards
            shards = random.randint(200, 500)
            xp = 50
        else:
            shards = random.randint(50, 100)
            xp = 20

    # Apply rewards
    update_query = {"$inc": {"balance": shards}}
    await user_collection.update_one(get_user_id_query(user_id), update_query)
    await add_xp(user_id, xp)

    if character_reward:
        from Grabber.core.user import add_char_to_user
        await add_char_to_user(user_id, character_reward)

    return {
        "shards": shards,
        "xp": xp,
        "character": character_reward
    }

async def get_random_character(rarities: list[str]) -> Optional[dict]:
    """Fetches a random character of specified rarities."""
    cursor = await collection.aggregate([
        {"$match": {"rarity": {"$in": rarities}}},
        {"$sample": {"size": 1}}
    ])
    res = await cursor.to_list(length=1)
    if res:
        char = res[0]
        # Clean up character dict for harem storage
        return {
            "id": char["id"],
            "name": char["name"],
            "anime": char["anime"],
            "rarity": char["rarity"],
            "img_url": char["img_url"]
        }
    return None
