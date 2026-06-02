import asyncio
import random
from datetime import datetime, timedelta, timezone
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import WEB_APP_URL, app, user_collection
from Grabber.core.keyboard import get_webapp_button
from Grabber.core.progression import add_xp, get_progress_bar
from Grabber.core.user import add_user_set_on_insert, get_user_filter
from Grabber.core.utils import get_user_id_query, handle_errors, html_escape

QUEST_POOL = {
    "catch_master": {
        "name": "Catch Master",
        "description": "Catch 2 characters",
        "target": 2,
        "reward_xp": 50,
        "reward_shards": 500,
        "icon": "◉",
        "symbol": "◉"
    },
    "guesser": {
        "name": "Quick Thinker",
        "description": "Identify 3 characters in /nguess",
        "target": 3,
        "reward_xp": 60,
        "reward_shards": 600,
        "icon": "🧩",
        "symbol": "🧩"
    },
    "battle_veteran": {
        "name": "Brawler",
        "description": "Win 1 battle",
        "target": 1,
        "reward_xp": 75,
        "reward_shards": 750,
        "icon": "⚔",
        "symbol": "⚔"
    },
    "egg_hunter": {
        "name": "Egg Seeker",
        "description": "Find 1 egg while hunting",
        "target": 1,
        "reward_xp": 40,
        "reward_shards": 400,
        "icon": "🥚",
        "symbol": "🥚"
    },
    "egg_hatcher": {
        "name": "Nurturer",
        "description": "Hatch 1 egg",
        "target": 1,
        "reward_xp": 50,
        "reward_shards": 500,
        "icon": "🐣",
        "symbol": "🐣"
    },
    "generous_soul": {
        "name": "Gift Giver",
        "description": "Gift Shards to a player",
        "target": 1,
        "reward_xp": 40,
        "reward_shards": 400,
        "icon": "🎁",
        "symbol": "🎁"
    },
    "trader": {
        "name": "Deal Maker",
        "description": "Complete a trade",
        "target": 1,
        "reward_xp": 50,
        "reward_shards": 500,
        "icon": "🤝",
        "symbol": "🤝"
    },
    "big_spender": {
        "name": "Big Spender",
        "description": "Spend 1,000 Shards",
        "target": 1000,
        "reward_xp": 100,
        "reward_shards": 1000,
        "icon": "💰",
        "symbol": "💰"
    }
}
WEEKLY_POOL = {
    "weekly_catch": {
        "name": "Master Collector",
        "description": "Catch 20 characters this week",
        "target": 20,
        "reward_xp": 500,
        "reward_shards": 5000,
        "icon": "❂",
        "symbol": "❂"
    },
    "weekly_guesser": {
        "name": "Enigma Master",
        "description": "Identify 15 characters in /nguess",
        "target": 15,
        "reward_xp": 600,
        "reward_shards": 6000,
        "icon": "🔮",
        "symbol": "🔮"
    },
    "weekly_hatcher": {
        "name": "Pro Breeder",
        "description": "Hatch 5 eggs this week",
        "target": 5,
        "reward_xp": 500,
        "reward_shards": 5000,
        "icon": "🕊",
        "symbol": "🕊"
    },
    "weekly_battle": {
        "name": "Warlord",
        "description": "Win 10 battles this week",
        "target": 10,
        "reward_xp": 600,
        "reward_shards": 6000,
        "icon": "⚔",
        "symbol": "⚔"
    },
    "weekly_spender": {
        "name": "Tycoon",
        "description": "Spend 10,000 Shards this week",
        "target": 10000,
        "reward_xp": 800,
        "reward_shards": 8000,
        "icon": "💎",
        "symbol": "💎"
    }
}
PASS_MISSIONS = {
    "pass_battles": {
        "name": "Pass Warlord",
        "description": "Win 20 battles",
        "target": 20,
        "reward_xp": 1000,
        "reward_shards": 10000,
        "icon": "⚔",
        "symbol": "⚔"
    },
    "pass_collector": {
        "name": "Pass Master",
        "description": "Catch 50 characters",
        "target": 50,
        "reward_xp": 1000,
        "reward_shards": 10000,
        "icon": "❂",
        "symbol": "❂"
    },
    "pass_hatcher": {
        "name": "Pass Hatcher",
        "description": "Hatch 10 eggs",
        "target": 10,
        "reward_xp": 1500,
        "reward_shards": 15000,
        "icon": "🐣",
        "symbol": "🐣"
    }
}
async def get_user_quests(user_id: int) -> dict:
    user = await user_collection.find_one(get_user_filter(user_id))
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    current_week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]}"
    if not user:
        daily_keys = random.sample(list(QUEST_POOL.keys()), 3)
        weekly_keys = list(WEEKLY_POOL.keys())
        pass_keys = list(PASS_MISSIONS.keys())
        quests_data = {
            **{k: {"progress": 0, "claimed": False} for k in daily_keys},
            **{k: {"progress": 0, "claimed": False} for k in weekly_keys},
            **{k: {"progress": 0, "claimed": False} for k in pass_keys}
        }
        await user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert({
                "$set": {
                    "quests": quests_data,
                    "quests_reset_date": today,
                    "quests_week": current_week
                }
            }, user_id),
            upsert=True
        )
        return quests_data
    quests_data = user.get("quests", {})
    updates = {}
    last_reset = user.get("quests_reset_date")
    if last_reset != today:
        daily_keys = random.sample(list(QUEST_POOL.keys()), 3)
        quests_data = {k: v for k, v in quests_data.items() if k in WEEKLY_POOL or k in PASS_MISSIONS}
        quests_data.update({k: {"progress": 0, "claimed": False} for k in daily_keys})
        updates["quests_reset_date"] = today
    last_week = user.get("quests_week")
    if last_week != current_week:
        weekly_keys = list(WEEKLY_POOL.keys())
        pass_keys = list(PASS_MISSIONS.keys())
        for k in weekly_keys + pass_keys:
            quests_data[k] = {"progress": 0, "claimed": False}
        updates["quests_week"] = current_week
    if updates:
        updates["quests"] = quests_data
        await user_collection.update_one({"id": {"$in": [user_id, str(user_id)]}}, {"$set": updates})
    return quests_data
async def update_quest_progress(user_id: int, quest_id: str, increment: int = 1):
    """
    Fast-path quest progress update: attempts a direct $inc without calling get_user_quests.
    Falls back to the full read only when the quest key isn't present yet (new day / new user).
    """
    # Determine target without a DB read
    if quest_id in QUEST_POOL:
        target = QUEST_POOL[quest_id]["target"]
    elif quest_id in WEEKLY_POOL:
        target = WEEKLY_POOL[quest_id]["target"]
    elif quest_id in PASS_MISSIONS:
        target = PASS_MISSIONS[quest_id]["target"]
    else:
        return
    # Try direct update — only touches the document if the quest key exists and isn't claimed
    quest_filter = get_user_id_query(user_id)
    quest_filter[f"quests.{quest_id}.claimed"] = False
    quest_filter[f"quests.{quest_id}.progress"] = {"$lt": target}
    result = await user_collection.update_one(
        quest_filter,
        {"$inc": {f"quests.{quest_id}.progress": increment}}
    )
    if result.matched_count == 0:
        # Quest key is missing (new user/day reset) — fall back to slow initializer
        quests = await get_user_quests(user_id)
        if quest_id in quests and quests[quest_id]["progress"] < target:
            await user_collection.update_one(
                get_user_id_query(user_id),
                {"$set": {f"quests.{quest_id}.progress": min(quests[quest_id]["progress"] + increment, target)}}
            )
@app.on_message(filters.command("quests"))
@handle_errors
async def view_quests(_, message: types.Message, edit_message=False):
    user_id = message.from_user.id if hasattr(message, 'from_user') and message.from_user else message.chat.id
    quests = await get_user_quests(user_id)
    if not quests:
        if edit_message:
            await message.edit_text("🚫 No quests available right now.", parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text("🚫 No quests available right now.", parse_mode=enums.ParseMode.HTML)
        return
    text = "<b>Quest Log</b>\n\n"
    buttons = []
    text += "<b>Daily Quests</b>\n"
    has_daily = False
    for qid, qdata in quests.items():
        if qid not in QUEST_POOL: continue
        has_daily = True
        info = QUEST_POOL[qid]
        prog = qdata["progress"]
        targ = info["target"]
        claimed = qdata["claimed"]
        bar = get_progress_bar(prog, targ, 6)
        if claimed:
            status = "✅"
            btn_txt = f"{info['icon']} {info['name']} ✅"
        elif prog >= targ:
            status = "🎁"
            btn_txt = f"{info['icon']} Claim {info['name']}"
            buttons.append([types.InlineKeyboardButton(btn_txt, callback_data=f"quest_claim:{qid}")])
        else:
            status = f"<code>{prog}/{targ}</code>"
        text += f"{info['icon']} <b>{info['name']}</b>: {bar} {status}\n"
    if not has_daily: text += "<i>No daily quests active.</i>\n"
    text += "\n"
    text += "<b>Weekly Challenges</b>\n"
    has_weekly = False
    for qid, qdata in quests.items():
        if qid not in WEEKLY_POOL: continue
        has_weekly = True
        info = WEEKLY_POOL[qid]
        prog = qdata["progress"]
        targ = info["target"]
        claimed = qdata["claimed"]
        bar = get_progress_bar(prog, targ, 6)
        if claimed:
            status = "✅"
            btn_txt = f"{info['icon']} {info['name']} ✅"
        elif prog >= targ:
            status = "🎁"
            btn_txt = f"{info['icon']} Claim {info['name']}"
            buttons.append([types.InlineKeyboardButton(btn_txt, callback_data=f"quest_claim:{qid}")])
        else:
            status = f"<code>{prog}/{targ}</code>"
        text += f"{info['icon']} <b>{info['name']}</b>: {bar} {status}\n"
    text += "\n<b>Pass Missions</b>\n"
    has_pass = False
    for qid, qdata in quests.items():
        if qid not in PASS_MISSIONS: continue
        has_pass = True
        info = PASS_MISSIONS[qid]
        prog = qdata["progress"]
        targ = info["target"]
        claimed = qdata["claimed"]
        bar = get_progress_bar(prog, targ, 6)
        if claimed:
            status = "✅"
            btn_txt = f"{info['icon']} {info['name']} ✅"
        elif prog >= targ:
            status = "🎁"
            btn_txt = f"{info['icon']} Claim {info['name']}"
            buttons.append([types.InlineKeyboardButton(btn_txt, callback_data=f"quest_claim:{qid}")])
        else:
            status = f"<code>{prog}/{targ}</code>"
        text += f"{info['icon']} <b>{info['name']}</b>: {bar} {status}\n"
    now = datetime.now(timezone.utc)
    tmrw = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    d_left = tmrw - now
    days_until_mon = (7 - now.weekday()) % 7
    if days_until_mon == 0 and d_left.total_seconds() < 86400: days_until_mon = 7
    text += f"\n<b>Daily Reset:</b> <code>{int(d_left.total_seconds()//3600)}h</code>\n"
    text += f"<b>Weekly Reset:</b> <code>{days_until_mon} days</code>"
    if not buttons:
        buttons = []
    from Grabber.core.keyboard import get_webapp_button
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#quests")
    if webapp_btn:
        buttons.append([webapp_btn])
    markup = types.InlineKeyboardMarkup(buttons)
    if edit_message:
        try:
            await message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
        except Exception:
            pass
    else:
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
@app.on_callback_query(filters.regex(r"^quest_claim:"))
async def claim_quest_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    quest_id = query.data.split(":")[1]
    if quest_id in QUEST_POOL:
        quest_info = QUEST_POOL[quest_id]
    elif quest_id in WEEKLY_POOL:
        quest_info = WEEKLY_POOL[quest_id]
    elif quest_id in PASS_MISSIONS:
        quest_info = PASS_MISSIONS[quest_id]
        user_raw = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
        pass_type = user_raw.get("pass_type", "free") if user_raw else "free"
        if pass_type == "free":
            return await query.answer("This mission requires a Premium or Elite Pass!", show_alert=True)
    else:
        return await query.answer("Quest not found!", show_alert=True)
    result = await user_collection.update_one(
        {
            "id": {"$in": [user_id, str(user_id)]},
            f"quests.{quest_id}.claimed": {"$ne": True},
            f"quests.{quest_id}.progress": {"$gte": quest_info["target"]}
        },
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    if result.modified_count == 0:
        return await query.answer("Already claimed or quest not complete!", show_alert=True)
    reward_xp = quest_info["reward_xp"]
    reward_shards = quest_info.get("reward_shards", 0)

    await add_xp(user_id, reward_xp, f"quest_{quest_id}")
    if reward_shards > 0:
        await user_collection.update_one(
            {"id": {"$in": [user_id, str(user_id)]}},
            {"$inc": {"balance": reward_shards}}
        )

    await query.answer(f"Claimed! +{reward_xp} XP & +{reward_shards} Shards!", show_alert=True)
    await view_quests(None, query.message, edit_message=True)
