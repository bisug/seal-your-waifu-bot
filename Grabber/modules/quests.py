from datetime import datetime, timedelta
from pyrogram import filters, types, enums
from Grabber import user_collection, app
from Grabber.core.progression import add_xp, get_progress_bar

# Quest Definitions
DAILY_QUESTS = {
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
    }
}

async def get_user_quests(user_id: int) -> dict:
    """Get user's quest progress, resetting if it's a new day."""
    user = await user_collection.find_one({"id": user_id})
    
    if not user:
        # Initialize quests
        quests_data = {quest_id: {"progress": 0, "claimed": False} for quest_id in DAILY_QUESTS}
        await user_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "quests": quests_data,
                    "quests_reset_date": datetime.utcnow().date().isoformat()
                }
            },
            upsert=True
        )
        return quests_data
    
    # Check if quests need to be reset (new day)
    last_reset = user.get("quests_reset_date")
    today = datetime.utcnow().date().isoformat()
    
    if last_reset != today:
        # Reset quests for new day
        quests_data = {quest_id: {"progress": 0, "claimed": False} for quest_id in DAILY_QUESTS}
        await user_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "quests": quests_data,
                    "quests_reset_date": today
                }
            }
        )
        return quests_data
    
    return user.get("quests", {quest_id: {"progress": 0, "claimed": False} for quest_id in DAILY_QUESTS})

async def update_quest_progress(user_id: int, quest_id: str, increment: int = 1):
    """Update progress for a specific quest."""
    quests = await get_user_quests(user_id)
    
    if quest_id not in quests:
        return
    
    quest = quests[quest_id]
    target = DAILY_QUESTS[quest_id]["target"]
    
    # Only update if not completed
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
    
    text = "📋 <b>Daily Quests</b>\n\n"
    
    buttons = []
    for quest_id, quest_data in quests.items():
        quest_info = DAILY_QUESTS[quest_id]
        progress = quest_data.get("progress", 0)
        target = quest_info["target"]
        claimed = quest_data.get("claimed", False)
        
        # Progress bar
        progress_bar = get_progress_bar(progress, target, 8)
        
        # Status
        if claimed:
            status = "✅ Claimed"
            button_text = f"{quest_info['icon']} {quest_info['name']} ✅"
        elif progress >= target:
            status = "🎁 Ready!"
            button_text = f"{quest_info['icon']} Claim {quest_info['name']}"
            buttons.append([types.InlineKeyboardButton(button_text, callback_data=f"quest_claim:{quest_id}")])
        else:
            status = f"{progress}/{target}"
        
        text += (
            f"{quest_info['icon']} <b>{quest_info['name']}</b>\n"
            f"   {quest_info['description']}\n"
            f"   {progress_bar} {status}\n"
            f"   Reward: <b>+{quest_info['reward_xp']} XP</b>\n\n"
        )
    
    # Calculate time until reset
    now = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_left = tomorrow - now
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    
    text += f"⏰ <i>Resets in {hours}h {minutes}m</i>"
    
    markup = types.InlineKeyboardMarkup(buttons) if buttons else None
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^quest_claim:"))
async def claim_quest_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    quest_id = query.data.split(":")[1]
    
    quests = await get_user_quests(user_id)
    quest_data = quests.get(quest_id, {})
    quest_info = DAILY_QUESTS.get(quest_id)
    
    if not quest_info:
        return await query.answer("❌ Quest not found!", show_alert=True)
    
    # Check if already claimed
    if quest_data.get("claimed", False):
        return await query.answer("❌ Already claimed!", show_alert=True)
    
    # Check if completed
    if quest_data.get("progress", 0) < quest_info["target"]:
        return await query.answer("❌ Quest not completed yet!", show_alert=True)
    
    # Grant XP
    reward_xp = quest_info["reward_xp"]
    await add_xp(user_id, reward_xp, f"quest_{quest_id}")
    
    # Mark as claimed
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    
    await query.answer(f"🎉 +{reward_xp} XP!", show_alert=True)
    
    # Refresh quest display
    quests = await get_user_quests(user_id)
    
    text = "📋 <b>Daily Quests</b>\n\n"
    buttons = []
    
    for qid, qdata in quests.items():
        qinfo = DAILY_QUESTS[qid]
        progress = qdata.get("progress", 0)
        target = qinfo["target"]
        claimed = qdata.get("claimed", False)
        
        progress_bar = get_progress_bar(progress, target, 8)
        
        if claimed:
            status = "✅ Claimed"
        elif progress >= target:
            status = "🎁 Ready!"
            buttons.append([types.InlineKeyboardButton(f"{qinfo['icon']} Claim {qinfo['name']}", callback_data=f"quest_claim:{qid}")])
        else:
            status = f"{progress}/{target}"
        
        text += (
            f"{qinfo['icon']} <b>{qinfo['name']}</b>\n"
            f"   {qinfo['description']}\n"
            f"   {progress_bar} {status}\n"
            f"   Reward: <b>+{qinfo['reward_xp']} XP</b>\n\n"
        )
    
    now = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_left = tomorrow - now
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    
    text += f"⏰ <i>Resets in {hours}h {minutes}m</i>"
    
    try:
        await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons) if buttons else None)
    except:
        pass
