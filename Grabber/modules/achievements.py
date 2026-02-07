from Grabber import user_collection, app, LOGGER
from Grabber.core.progression import add_xp
from pyrogram import enums

# Achievement Definitions
ACHIEVEMENTS = {
    "novice_collector": {
        "name": "Novice Collector",
        "description": "Own 10 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 10,
        "reward_xp": 100,
        "title": "Rookie"
    },
    "expert_collector": {
        "name": "Expert Collector",
        "description": "Own 100 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 100,
        "reward_xp": 1000,
        "title": "Curator"
    },
    "battle_hardened": {
        "name": "Battle Hardened",
        "description": "Win 50 Battles",
        "condition": lambda u: u.get("stats", {}).get("wins", 0) >= 50,
        "reward_xp": 500,
        "title": "Gladiator"
    },
    "rich_vip": {
        "name": "Millionaire",
        "description": "Hold 1,000,000 Coins",
        "condition": lambda u: u.get("balance", 0) >= 1000000,
        "title": "Tycoon 🎩",
        "reward_xp": 2000
    },
    "influencer": {
        "name": "Influencer",
        "description": "Invite 10 Users",
        "condition": lambda u: u.get("referrals_count", 0) >= 10,
        "title": "Ambassador 🤝",
        "reward_xp": 1000
    }
}

async def check_achievements(user_id: int):
    """Check if user qualifies for any new achievements."""
    user = await user_collection.find_one({"id": user_id})
    if not user: return
    
    user_achievements = user.get("achievements", [])
    new_unlocks = []
    
    for ach_id, data in ACHIEVEMENTS.items():
        if ach_id in user_achievements:
            continue
            
        # Check condition
        try:
            if data["condition"](user):
                new_unlocks.append(ach_id)
                # Grant Reward
                await add_xp(user_id, data["reward_xp"], f"ach_{ach_id}")
                
                # Notify User (via log for now, can add DM)
                LOGGER.info(f"User {user_id} unlocked {data['name']}")
                
                # Store Logic
                await user_collection.update_one(
                    {"id": user_id},
                    {
                        "$push": {"achievements": ach_id},
                        "$addToSet": {"titles": data["title"]} # Unlock title
                    }
                )
        except Exception as e:
            LOGGER.error(f"Error checking achievement {ach_id}: {e}")
            
    return new_unlocks
