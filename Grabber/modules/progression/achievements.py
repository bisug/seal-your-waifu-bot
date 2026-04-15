from pyrogram import enums
from pyrogram.enums import ParseMode

from Grabber import LOGGER, app, user_collection
from Grabber.core.progression import add_xp

ACHIEVEMENTS = {
    "novice_collector": {
        "name": "Novice Collector",
        "description": "Own 10 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 10,
        "reward_xp": 100,
        "title": "Rookie",
        "symbol": "◆"
    },
    "expert_collector": {
        "name": "Expert Collector",
        "description": "Own 100 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 100,
        "reward_xp": 1000,
        "title": "Curator",
        "symbol": "◈"
    },
    "battle_hardened": {
        "name": "Battle Hardened",
        "description": "Win 50 Battles",
        "condition": lambda u: u.get("stats", {}).get("wins", 0) >= 50,
        "reward_xp": 500,
        "title": "Gladiator",
        "symbol": "⚔"
    },
    "rich_vip": {
        "name": "Millionaire",
        "description": "Hold 1,000,000 Shards",
        "condition": lambda u: u.get("balance", 0) >= 1000000,
        "title": "Tycoon",
        "reward_xp": 2000,
        "symbol": "✧"
    },
    "influencer": {
        "name": "Influencer",
        "description": "Invite 10 Users",
        "condition": lambda u: u.get("referrals_count", 0) >= 10,
        "title": "Ambassador",
        "reward_xp": 1000,
        "symbol": "❃"
    }
}

async def check_achievements(user_id: int):

    user = await user_collection.find_one({"id": user_id})
    if not user: return

    user_achievements = set(user.get("achievements", []))
    new_unlocks = []

    for ach_id, data in ACHIEVEMENTS.items():
        if ach_id in user_achievements:
            continue

        try:
            if data["condition"](user):
                new_unlocks.append((ach_id, data))
        except Exception as e:
            LOGGER.error(f"Error checking achievement {ach_id}: {e}")

    if not new_unlocks:
        return []

    # Grant XP for each unlock (kept sequential — has level-up side effects)
    for ach_id, data in new_unlocks:
        await add_xp(user_id, data["reward_xp"], f"ach_{ach_id}")
        LOGGER.info(f"User {user_id} unlocked {data['name']}")

    # Single batch write for all new achievement IDs + titles
    new_ach_ids = [a[0] for a in new_unlocks]
    new_titles = [a[1]["title"] for a in new_unlocks]
    await user_collection.update_one(
        {"id": user_id},
        {
            "$push": {"achievements": {"$each": new_ach_ids}},
            "$addToSet": {"titles": {"$each": new_titles}}
        }
    )

    return new_ach_ids
