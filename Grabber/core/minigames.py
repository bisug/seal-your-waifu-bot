import time
import random
import json
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
        if last_recharge_dt.tzinfo is None:
            last_recharge_dt = last_recharge_dt.replace(tzinfo=timezone.utc)
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

async def consume_energy(user_id: int, game_type: Optional[str] = None) -> Any:
    """Consumes 1 energy point if available. Optionally starts a session and returns start data."""
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

    # Atomic guard: only decrement when energy is still >= 1 so concurrent
    # start requests cannot double-spend the same point into negative energy.
    consume_filter = get_user_id_query(user_id)
    consume_filter["energy"] = {"$gte": 1}
    result = await user_collection.update_one(consume_filter, update_fields)
    if result.modified_count == 0:
        return False

    start_data = {"start_time": now.timestamp()}

    if game_type == "cipher_match":
        # Get 8 random characters for the grid
        cursor = await collection.aggregate([{"$sample": {"size": 8}}])
        chars = await cursor.to_list(length=8)
        start_data["cards"] = [{
            "id": c["id"],
            "img_url": c["img_url"],
            "name": c["name"]
        } for c in chars]
    elif game_type == "nexus_wheel":
        # Pre-roll the reward based on wheel sectors
        roll = random.random()
        if roll < 0.05: # 5% Character
            index = 3
        elif roll < 0.15: # 10% 500 Shards
            index = 5
        elif roll < 0.30: # 15% 200 Shards
            index = 2
        elif roll < 0.45: # 15% 150 Shards
            index = 4
        elif roll < 0.60: # 15% 100 Shards
            index = 1
        elif roll < 0.75: # 15% 80 Shards
            index = 6
        elif roll < 0.90: # 15% 50 Shards
            index = 0
        else: # 10% XP Boost
            index = 7

        prizes = [
            {"type": "shards", "amount": 50, "label": "50 Shards"},
            {"type": "shards", "amount": 100, "label": "100 Shards"},
            {"type": "shards", "amount": 200, "label": "200 Shards"},
            {"type": "character", "label": "Character"},
            {"type": "shards", "amount": 150, "label": "150 Shards"},
            {"type": "shards", "amount": 500, "label": "500 Shards"},
            {"type": "shards", "amount": 80, "label": "80 Shards"},
            {"type": "xp", "amount": 0, "label": "XP Boost"}
        ]
        start_data["prize"] = prizes[index]
        start_data["prize_index"] = index

    if game_type and r:
        session_key = f"minigame_session:{user_id}:{game_type}"
        await r.set(session_key, json.dumps(start_data), ex=300) # 5 min session

    await invalidate_user_cache(user_id)
    return start_data if game_type else True

async def validate_session(user_id: int, game_type: str) -> Optional[dict]:
    """Returns session data if valid, or None if no session."""
    if not r:
        return {"start_time": get_now_utc().timestamp() - 10} # Fallback if no redis

    session_key = f"minigame_session:{user_id}:{game_type}"
    session_data_str = await r.get(session_key)
    if not session_data_str:
        return None

    await r.delete(session_key)
    return json.loads(session_data_str)

async def reward_minigame(user_id: int, game_type: str, score: int = 0, session_data: dict = None) -> Dict[str, Any]:
    """Calculates and applies rewards for mini-games."""
    if not session_data:
        return {"error": "Invalid session data"}

    time_taken = get_now_utc().timestamp() - session_data.get("start_time", 0)

    # Basic rewards
    shards = 0
    xp = 0
    character_reward = None

    if game_type == "cipher_match":
        # Anti-cheat: 8 pairs matched in less than 5 seconds is highly suspicious
        if score >= 8 and time_taken < 5.0:
             LOGGER.warning(f"User {user_id} suspicious Cipher Match: {score} pairs in {time_taken}s")
             return {"error": "Suspicious activity detected"}

        if score < 4:
            return {"error": "Mission failed: Insufficient data collected"}

        # Score is pairs matched (max 8)
        base_shards = score * 25
        shards = base_shards + random.randint(20, 100)
        xp = score * 5 + random.randint(5, 15)

        # Bonus for speed
        if score == 8 and time_taken < 25:
            shards += 100
            xp += 30

    elif game_type == "nexus_wheel":
        prize = session_data.get("prize")
        if not prize:
             return {"error": "No prize determined in session"}

        if prize["type"] == "character":
            character_reward = await get_random_character(["⚪ Common", "🟢 Medium", "🟡 Rare"])
            shards = 100
            xp = 25
        elif prize["type"] == "xp":
            shards = 50
            xp = 250
        else:
            shards = prize.get("amount", 50)
            xp = shards // 10 + 5

    # Apply rewards
    update_query = {"$inc": {"balance": shards}}
    await user_collection.update_one(get_user_id_query(user_id), update_query)
    await add_xp(user_id, xp)

    if character_reward:
        from Grabber.core.user import add_char_to_user
        await add_char_to_user(user_id, character_reward)

    # Balance/XP were mutated outside the cached-document path; drop the stale
    # Redis copy so the WebApp reflects rewards immediately.
    await invalidate_user_cache(user_id)

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
