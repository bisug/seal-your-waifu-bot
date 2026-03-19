from Grabber.database import user_collection
from Grabber import LOGGER


LEVEL_CAP = 50


LEVEL_REWARDS = {
    5: {"free": 1000, "premium": 3000, "elite": 5000},
    10: {"free": "egg_common", "premium": "egg_gold", "elite": "egg_void"},
    25: {"free": 5000, "premium": 15000, "elite": 25000},
    50: {"free": 10000, "premium": 30000, "elite": 50000}
}

def get_level_from_xp(xp: int) -> int:
    """
    Calculate the current level based on total XP.
    Levels have increasing XP requirements.
    """
    level = 0
    required_xp = 100
    remaining_xp = xp

    while remaining_xp >= required_xp and level < LEVEL_CAP:
        remaining_xp -= required_xp
        level += 1
        required_xp = 100 * (level + 1)

    return level

def get_xp_for_next_level(current_level: int) -> int:
    """
    Calculate the total XP required to reach the next level.
    """
    if current_level >= LEVEL_CAP:
        return 0
    return 100 * (current_level + 1)

def get_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Generate a visual progress bar string.
    """
    if total == 0:
        return "[" + "░" * length + "]"

    filled = int((current / total) * length)
    empty = length - filled
    return "[" + "█" * filled + "░" * empty + "]"

async def add_xp(user_id: int, amount: int, source: str = "unknown"):
    """
    Add XP to a user's profile and handle level-ups atomically.
    """
    user = await user_collection.find_one_and_update(
        {"id": {"$in": [user_id, str(user_id)]}},
        {
            "$inc": {"xp": amount},
            "$setOnInsert": {
                "pass_type": "free",
                "claimed_levels": [],
                "season": 1
            }
        },
        upsert=True,
        return_document=True
    )

    if not user:
        return

    new_xp = user.get("xp", 0)
    old_xp = new_xp - amount
    old_level = get_level_from_xp(old_xp)
    new_level = get_level_from_xp(new_xp)

    LOGGER.info(f"User {user_id} gained {amount} XP from {source}. Level: {old_level} -> {new_level}")

    if new_level > old_level:
        await check_and_grant_rewards(user_id, old_level, new_level, user)

async def check_and_grant_rewards(user_id: int, old_level: int, new_level: int, user_data: dict = None):
    """
    Iterate through newly reached levels and grant corresponding rewards
    based on the user's Battle Pass type. Also tracks Pass Bank for free users.
    """
    if user_data is None:
        user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    else:
        user = user_data
        
    pass_type = user.get("pass_type", "free")
    claimed_levels = set(user.get("claimed_levels", []))
    
    from Grabber.core.pass_data import PASS_TRACKS
    import uuid

    total_coins_earned = 0
    eggs_awarded = []
    
    bank_shards = 0
    bank_eggs = {} # tier: count

    def add_egg(tier):
        eggs_awarded.append({
            "id": str(uuid.uuid4()),
            "tier": str(tier),
            "status": "fresh"
        })

    def bank_egg(tier):
        tier_str = str(tier)
        bank_eggs[tier_str] = bank_eggs.get(tier_str, 0) + 1

    for level in range(old_level + 1, new_level + 1):
        if level in claimed_levels:
            continue
            
        claimed_levels.add(level)
        track = PASS_TRACKS.get(level)
        
        if not track:
            # Fallback scaling for level > 100
            reward = 100 + (level * 2) if pass_type == "free" else 300 + (level * 4) if pass_type == "premium" else 500 + (level * 6)
            total_coins_earned += reward
            continue

        # Grant Free Reward (everyone gets this)
        free_rw = track["free"]
        if free_rw["type"] == "shards":
            total_coins_earned += free_rw["amount"]
        elif free_rw["type"] == "egg":
            add_egg(free_rw["tier"])

        # Grant Premium Reward (Premium & Elite get this)
        prem_rw = track["premium"]
        prem_extra = track.get("premium_extra_amount", 0)
        
        if pass_type in ["premium", "elite"]:
            if prem_rw["type"] == "shards":
                total_coins_earned += prem_rw["amount"]
            elif prem_rw["type"] == "egg":
                add_egg(prem_rw["tier"])
            total_coins_earned += prem_extra
        else:
            # FREE user: Bank premium rewards!
            if prem_rw["type"] == "shards":
                bank_shards += prem_rw["amount"]
            elif prem_rw["type"] == "egg":
                bank_egg(prem_rw["tier"])
            bank_shards += prem_extra

        # Grant Elite Reward (Elite only)
        elite_rw = track["elite"]
        elite_extra = track.get("elite_extra_amount", 0)
        
        if pass_type == "elite":
            if elite_rw["type"] == "shards":
                total_coins_earned += elite_rw["amount"]
            elif elite_rw["type"] == "egg":
                add_egg(elite_rw["tier"])
            total_coins_earned += elite_extra
        elif pass_type in ["free", "premium"]:
            # Bank elite rewards for non-elite users
            if elite_rw["type"] == "shards":
                bank_shards += elite_rw["amount"]
            elif elite_rw["type"] == "egg":
                bank_egg(elite_rw["tier"])
            bank_shards += elite_extra

    # Perform DB Updates
    updates = {"$set": {"claimed_levels": list(claimed_levels)}}
    if total_coins_earned > 0:
        updates.setdefault("$inc", {})["balance"] = total_coins_earned
        
    if bank_shards > 0:
        updates.setdefault("$inc", {})["pass_bank.shards"] = bank_shards
    for tier, count in bank_eggs.items():
        updates.setdefault("$inc", {})[f"pass_bank.eggs_t{tier}"] = count
        
    if eggs_awarded:
        updates["$push"] = {"eggs": {"$each": eggs_awarded}}

    if updates.get("$inc") or updates.get("$push") or updates.get("$set"):
        await user_collection.update_one(
            {"id": {"$in": [user_id, str(user_id)]}},
            updates
        )
        if total_coins_earned > 0 or eggs_awarded:
            LOGGER.info(f"User {user_id} pass rewards: {total_coins_earned} shards, {len(eggs_awarded)} eggs")

async def get_user_progress(user_id: int, user_data: dict = None) -> dict:
    """
    Retrieve a comprehensive summary of a user's progression state.
    Supports lazy loading by passing existing user_data to avoid DB lookup.
    """
    if user_data is None:
        user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    else:
        user = user_data

    if not user:
        return {
            "level": 0,
            "xp": 0,
            "xp_current": 0,
            "xp_needed": 100,
            "pass_type": "free",
            "season": 1,
            "claimed_levels": []
        }

    total_xp = user.get("xp", 0)
    level = get_level_from_xp(total_xp)
    xp_needed = get_xp_for_next_level(level)

    # Optimized formula for sum of arithmetic progression: 100 * (1 + 2 + ... + n) = 50 * n * (n + 1)
    xp_for_previous_levels = 50 * level * (level + 1)
    xp_current = total_xp - xp_for_previous_levels

    return {
        "level": level,
        "xp": total_xp,
        "xp_current": xp_current,
        "xp_needed": xp_needed,
        "pass_type": user.get("pass_type", "free"),
        "season": user.get("season", 1),
        "claimed_levels": user.get("claimed_levels", [])
    }
