import asyncio
from datetime import datetime, timedelta
import random
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import md_escape
from Grabber import user_collection, app
from Grabber.core.progression import add_xp, get_progress_bar

                      
QUEST_POOL = {
    "catch_master": {
        "name": "Catch Master",
        "description": "Catch 5 characters",
        "target": 5,
        "reward_xp": 50,
        "icon": "🎯"
    },
    "battle_veteran": {
        "name": "Battle Veteran",
        "description": "Win 2 battles",
        "target": 2,
        "reward_xp": 75,
        "icon": "⚔️"
    },
    "egg_hunter": {
        "name": "Egg Hunter",
        "description": "Find 2 eggs while hunting",
        "target": 2,
        "reward_xp": 60,
        "icon": "🥚"
    },
    "generous_soul": {
        "name": "Generous Soul",
        "description": "Gift Shards to a player",
        "target": 1,
        "reward_xp": 40,
        "icon": "🎁"
    },
    "trader": {
        "name": "Trader",
        "description": "Complete a trade",
        "target": 1,
        "reward_xp": 50,
        "icon": "🤝"
    },
    "big_spender": {
        "name": "Big Spender",
        "description": "Spend 1,000 Shards / 5 Zenith",
        "target": 5,
        "reward_xp": 100,
        "icon": "💸"
    }
}

                       
WEEKLY_POOL = {
    "weekly_catch": {
        "name": "Master Collector",
        "description": "Catch 50 characters this week",
        "target": 50,
        "reward_xp": 500,
        "icon": "🏆"
    },
    "weekly_battle": {
        "name": "Warlord",
        "description": "Win 20 battles this week",
        "target": 20,
        "reward_xp": 600,
        "icon": "⚔️"
    },
    "weekly_spender": {
        "name": "Tycoon",
        "description": "Spend 50,000 Shards this week",
        "target": 50000,
        "reward_xp": 800,
        "icon": "⬪"
    }
}

async def get_user_quests(user_id: int) -> dict:
                                                                      
    user = await user_collection.find_one({"id": user_id})
    now = datetime.utcnow()
    today = now.date().isoformat()
                                                
    current_week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]}" 
    
    if not user:
                    
        daily_keys = random.sample(list(QUEST_POOL.keys()), 3)
        weekly_keys = list(WEEKLY_POOL.keys())                           
        
        quests_data = {
            **{k: {"progress": 0, "claimed": False} for k in daily_keys},
            **{k: {"progress": 0, "claimed": False} for k in weekly_keys}
        }
        
        await user_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "quests": quests_data,
                    "quests_reset_date": today,
                    "quests_week": current_week
                }
            },
            upsert=True
        )
        return quests_data
    
    quests_data = user.get("quests", {})
    updates = {}
    
                          
    last_reset = user.get("quests_reset_date")
    if last_reset != today:
        daily_keys = random.sample(list(QUEST_POOL.keys()), 3)
                                                         
        quests_data = {k: v for k, v in quests_data.items() if k in WEEKLY_POOL}
                              
        quests_data.update({k: {"progress": 0, "claimed": False} for k in daily_keys})
        
        updates["quests_reset_date"] = today
        
                           
    last_week = user.get("quests_week")
    if last_week != current_week:
        weekly_keys = list(WEEKLY_POOL.keys())
                               
        for k in weekly_keys:
            quests_data[k] = {"progress": 0, "claimed": False}
            
        updates["quests_week"] = current_week
            
    if updates:
        updates["quests"] = quests_data
        await user_collection.update_one({"id": user_id}, {"$set": updates})
        
    return quests_data

async def update_quest_progress(user_id: int, quest_id: str, increment: int = 1):
                                                                 
    quests = await get_user_quests(user_id)
    
                                                                                   
                                     
    
    if quest_id not in quests:
        return
    
    quest = quests[quest_id]
    
                   
    if quest_id in QUEST_POOL:
        target = QUEST_POOL[quest_id]["target"]
    elif quest_id in WEEKLY_POOL:
        target = WEEKLY_POOL[quest_id]["target"]
    else:
        return

                                  
    if quest["progress"] < target:
        new_progress = min(quest["progress"] + increment, target)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {f"quests.{quest_id}.progress": new_progress}}
        )

@app.on_message(filters.command("quests"))
async def view_quests(_, message: types.Message):
    user_id = message.from_user.id
    quests = await get_user_quests(user_id)
    
    if not quests:
        await message.reply_text("🚫 No quests available right now.", parse_mode=ParseMode.MARKDOWN)
        return

    text = "📋 **Quest Log**\n\n"
    buttons = []
    
                         
    text += "📅 **Daily Quests**\n"
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
            status = f"`{prog}/{targ}`"
            
        text += f"{info['icon']} **{info['name']}**: {bar} {status}\n"
    
    if not has_daily: text += "_No daily quests active._\n"
    text += "\n"
    
                          
    text += "🗓️ **Weekly Challenges**\n"
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
            status = f"`{prog}/{targ}`"
            
        text += f"{info['icon']} **{info['name']}**: {bar} {status}\n"

            
    now = datetime.utcnow()
    tmrw = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    d_left = tmrw - now
    
                       
    days_until_mon = (7 - now.weekday()) % 7
    if days_until_mon == 0 and d_left.total_seconds() < 86400: days_until_mon = 7                                     
    
    text += f"\n⏰ **Daily Reset:** `{int(d_left.total_seconds()//3600)}h`\n"
    text += f"🗓️ **Weekly Reset:** `{days_until_mon} days`"
    
    markup = types.InlineKeyboardMarkup(buttons) if buttons else None
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^quest_claim:"))
async def claim_quest_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    quest_id = query.data.split(":")[1]
    
    quests = await get_user_quests(user_id)
    quest_data = quests.get(quest_id, {})
    
                           
    if quest_id in QUEST_POOL:
        quest_info = QUEST_POOL[quest_id]
    elif quest_id in WEEKLY_POOL:
        quest_info = WEEKLY_POOL[quest_id]
    else:
        return await query.answer("❌ Quest not found!", show_alert=True)
    
    if quest_data.get("claimed", False):
        return await query.answer("❌ Already claimed!", show_alert=True)
    
    if quest_data.get("progress", 0) < quest_info["target"]:
        return await query.answer("❌ Quest not completed yet!", show_alert=True)
    
            
    reward_xp = quest_info["reward_xp"]
    await add_xp(user_id, reward_xp, f"quest_{quest_id}")
    
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    
    await query.answer(f"🎉 +{reward_xp} XP!", show_alert=True)
    
                                 
    await view_quests(None, query.message)
