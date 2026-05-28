from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, app, user_collection
from Grabber.core.progression import add_xp
ACHIEVEMENTS = {
    "collector_10": {
        "name": "Novice Collector",
        "description": "Own 10 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 10,
        "reward_xp": 100,
        "reward_shards": 1000,
        "title": "Rookie",
        "symbol": "🥉"
    },
    "collector_50": {
        "name": "Gatherer",
        "description": "Own 50 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 50,
        "reward_xp": 500,
        "reward_shards": 5000,
        "title": "Enthusiast",
        "symbol": "🥈"
    },
    "collector_100": {
        "name": "Expert Collector",
        "description": "Own 100 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 100,
        "reward_xp": 1000,
        "reward_shards": 10000,
        "title": "Curator",
        "symbol": "🥇"
    },
    "collector_250": {
        "name": "Master Collector",
        "description": "Own 250 Characters",
        "condition": lambda u: len(u.get("characters", [])) >= 250,
        "reward_xp": 2500,
        "reward_shards": 25000,
        "title": "Hoarder",
        "symbol": "🏆"
    },
    "guesser_10": {
        "name": "Sharp Eye",
        "description": "Correctly guess 10 characters",
        "condition": lambda u: u.get("guess_count", 0) >= 10,
        "reward_xp": 200,
        "reward_shards": 2000,
        "title": "Observer",
        "symbol": "🔍"
    },
    "hatcher_1": {
        "name": "First Hatch",
        "description": "Hatch your first egg",
        "condition": lambda u: u.get("hatch_count", 0) >= 1,
        "reward_xp": 150,
        "reward_shards": 1500,
        "title": "Caregiver",
        "symbol": "🐣"
    },
    "hatcher_10": {
        "name": "Egg Expert",
        "description": "Hatch 10 eggs",
        "condition": lambda u: u.get("hatch_count", 0) >= 10,
        "reward_xp": 1000,
        "reward_shards": 10000,
        "title": "Breeder",
        "symbol": "🥚"
    },
    "battle_hardened": {
        "name": "Battle Hardened",
        "description": "Win 50 Battles",
        "condition": lambda u: u.get("stats", {}).get("wins", 0) >= 50,
        "reward_xp": 500,
        "reward_shards": 5000,
        "title": "Gladiator",
        "symbol": "⚔"
    },
    "rich_vip": {
        "name": "Millionaire",
        "description": "Hold 1,000,000 Shards",
        "condition": lambda u: u.get("balance", 0) >= 1000000,
        "title": "Tycoon",
        "reward_xp": 2000,
        "reward_shards": 20000,
        "symbol": "✧"
    },
    "influencer": {
        "name": "Influencer",
        "description": "Invite 10 Users",
        "condition": lambda u: u.get("referrals_count", 0) >= 10,
        "title": "Ambassador",
        "reward_xp": 1000,
        "reward_shards": 10000,
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
    # Grant rewards for each unlock (kept sequential — has level-up side effects)
    total_shards = 0
    for ach_id, data in new_unlocks:
        await add_xp(user_id, data["reward_xp"], f"ach_{ach_id}")
        total_shards += data.get("reward_shards", 0)
        LOGGER.info(f"User {user_id} unlocked {data['name']}")

    # Single batch write for all new achievement IDs + titles + shards
    new_ach_ids = [a[0] for a in new_unlocks]
    new_titles = [a[1]["title"] for a in new_unlocks]

    update_op = {
        "$push": {"achievements": {"$each": new_ach_ids}},
        "$addToSet": {"titles": {"$each": new_titles}}
    }
    if total_shards > 0:
        update_op["$inc"] = {"balance": total_shards}

    await user_collection.update_one({"id": user_id}, update_op)
    return new_ach_ids
