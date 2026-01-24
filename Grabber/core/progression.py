from Grabber.database import user_collection
from Grabber import LOGGER

# Constants
LEVEL_CAP = 50

# Level Rewards Configuration
LEVEL_REWARDS = {
    5: {"free": 1000, "premium": 3000, "elite": 5000},
    10: {"free": "egg_common", "premium": "egg_gold", "elite": "egg_void"},
    25: {"free": 5000, "premium": 15000, "elite": 25000},
    50: {"free": 10000, "premium": 30000, "elite": 50000}
}

def get_level_from_xp(xp: int) -> int:
    """Calculate level from total XP."""
    level = 0
    required_xp = 100
    remaining_xp = xp
    
    while remaining_xp >= required_xp and level < LEVEL_CAP:
        remaining_xp -= required_xp
        level += 1
        required_xp = 100 * (level + 1)
    
    return level

def get_xp_for_next_level(current_level: int) -> int:
    """Get XP required for next level."""
    if current_level >= LEVEL_CAP:
        return 0
    return 100 * (current_level + 1)

def get_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Generate a visual progress bar."""
    if total == 0:
        return "[" + "░" * length + "]"
    
    filled = int((current / total) * length)
    empty = length - filled
    return "[" + "█" * filled + "░" * empty + "]"

async def add_xp(user_id: int, amount: int, source: str = "unknown"):
    """Add XP to user and check for level up."""
    user = await user_collection.find_one({"id": user_id})
    if not user:
        # Initialize user with XP
        await user_collection.insert_one({
            "id": user_id,
            "xp": amount,
            "pass_type": "free",
            "claimed_levels": [],
            "season": 1
        })
        LOGGER.info(f"User {user_id} gained {amount} XP from {source} (new profile)")
        return
    
    old_xp = user.get("xp", 0)
    new_xp = old_xp + amount
    old_level = get_level_from_xp(old_xp)
    new_level = get_level_from_xp(new_xp)
    
    # Update XP
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"xp": new_xp}}
    )
    
    LOGGER.info(f"User {user_id} gained {amount} XP from {source}. Level: {old_level} -> {new_level}")
    
    # Check for level up and grant rewards
    if new_level > old_level:
        await check_and_grant_rewards(user_id, old_level, new_level)

async def check_and_grant_rewards(user_id: int, old_level: int, new_level: int):
    """Check if any milestone levels were passed and grant rewards."""
    user = await user_collection.find_one({"id": user_id})
    pass_type = user.get("pass_type", "free")
    claimed_levels = set(user.get("claimed_levels", []))
    
    # Check each level between old and new
    for level in range(old_level + 1, new_level + 1):
        if level in LEVEL_REWARDS and level not in claimed_levels:
            reward = LEVEL_REWARDS[level].get(pass_type)
            
            if isinstance(reward, int):
                # Coin reward
                await user_collection.update_one(
                    {"id": user_id},
                    {"$inc": {"balance": reward}}
                )
                LOGGER.info(f"User {user_id} received {reward} coins for reaching level {level} ({pass_type})")
            
            elif isinstance(reward, str) and reward.startswith("egg_"):
                # Egg reward
                tier = reward.split("_")[1]
                egg_data = {
                    "id": f"reward_egg_{level}",
                    "tier": tier,
                    "name": f"🎁 Level {level} Reward Egg",
                    "status": "fresh"
                }
                await user_collection.update_one(
                    {"id": user_id},
                    {"$push": {"eggs": egg_data}}
                )
                LOGGER.info(f"User {user_id} received {tier} egg for reaching level {level} ({pass_type})")
            
            # Mark as claimed
            claimed_levels.add(level)
    
    # Update claimed levels
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"claimed_levels": list(claimed_levels)}}
    )

async def get_user_progress(user_id: int) -> dict:
    """Get detailed progression info for a user."""
    user = await user_collection.find_one({"id": user_id})
    
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
    
    # Calculate XP within current level
    xp_for_previous_levels = sum([100 * (i + 1) for i in range(level)])
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
