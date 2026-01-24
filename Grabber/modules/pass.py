from pyrogram import filters, types, enums
from Grabber import user_collection, app
from Grabber.core.progression import get_user_progress, get_progress_bar, LEVEL_REWARDS

# Pass Tier Prices
PASS_PRICES = {
    "premium": 500000,
    "elite": 1000000
}

# Pass Tier Emojis
PASS_EMOJI = {
    "free": "🆓",
    "premium": "⭐",
    "elite": "💎"
}

# /pass command - View status with visual progress
@app.on_message(filters.command("pass"))
async def view_pass(_, message: types.Message):
    user_id = message.from_user.id
    progress = await get_user_progress(user_id)
    
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"]
    season = progress["season"]
    
    # Visual progress bar
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100
    
    # Next milestone
    next_milestone = None
    for milestone_level in sorted(LEVEL_REWARDS.keys()):
        if milestone_level > level:
            next_milestone = milestone_level
            break
    
    text = (
        f"🎫 <b>Battle Pass - Season {season}</b>\n\n"
        f"{PASS_EMOJI[pass_type]} <b>Tier:</b> {pass_type.capitalize()}\n"
        f"⭐ <b>Level:</b> {level} / 50\n\n"
        f"<b>Progress to Level {level + 1}:</b>\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP\n\n"
    )
    
    if next_milestone:
        text += f"🎯 <b>Next Milestone:</b> Level {next_milestone}\n"
    
    # Show upgrade options if not elite
    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="buypass_premium")])
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    
    buttons.append([types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")])
    
    markup = types.InlineKeyboardMarkup(buttons)
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)

# Callback for buying pass tiers
@app.on_callback_query(filters.regex(r"^buypass_(premium|elite)$"))
async def buypass_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    tier = query.data.split("_")[1]
    price = PASS_PRICES[tier]
    
    user = await user_collection.find_one({"id": user_id})
    
    if not user:
        return await query.answer("❌ No profile found!", show_alert=True)
    
    current_tier = user.get("pass_type", "free")
    
    # Check if already owned or higher
    tiers_order = ["free", "premium", "elite"]
    if tiers_order.index(current_tier) >= tiers_order.index(tier):
        return await query.answer(f"✅ You already have {current_tier.capitalize()} or better!", show_alert=True)
    
    # Check balance
    if user.get("balance", 0) < price:
        return await query.answer(f"❌ Insufficient funds! Need {price:,} coins.", show_alert=True)
    
    # Purchase
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"pass_type": tier},
            "$inc": {"balance": -price}
        }
    )
    
    await query.answer(f"🎉 {tier.capitalize()} Pass activated!", show_alert=True)
    
    # Refresh display
    progress = await get_user_progress(user_id)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    season = progress["season"]
    
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100
    
    text = (
        f"🎫 <b>Battle Pass - Season {season}</b>\n\n"
        f"{PASS_EMOJI[tier]} <b>Tier:</b> {tier.capitalize()}\n"
        f"⭐ <b>Level:</b> {level} / 50\n\n"
        f"<b>Progress to Level {level + 1}:</b>\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP\n\n"
        f"✨ <i>Upgraded rewards active!</i>"
    )
    
    buttons = [[types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")]]
    if tier == "premium":
        buttons.insert(0, [types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    
    try:
        await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))
    except:
        pass

# View available rewards
@app.on_callback_query(filters.regex(r"^pass_rewards$"))
async def view_rewards_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    progress = await get_user_progress(user_id)
    
    pass_type = progress["pass_type"]
    level = progress["level"]
    claimed = set(progress["claimed_levels"])
    
    text = f"🎁 <b>Battle Pass Rewards</b>\n\n{PASS_EMOJI[pass_type]} <b>{pass_type.capitalize()} Tier</b>\n\n"
    
    for milestone in sorted(LEVEL_REWARDS.keys()):
        reward = LEVEL_REWARDS[milestone].get(pass_type, "None")
        
        # Format reward
        if isinstance(reward, int):
            reward_text = f"{reward:,} Coins"
        elif isinstance(reward, str) and reward.startswith("egg_"):
            tier_name = reward.split("_")[1].capitalize()
            reward_text = f"{tier_name} Egg"
        else:
            reward_text = "Special Reward"
        
        # Status
        if milestone in claimed:
            status = "✅"
        elif level >= milestone:
            status = "🎁"
        else:
            status = "🔒"
        
        text += f"{status} <b>Level {milestone}:</b> {reward_text}\n"
    
    buttons = [[types.InlineKeyboardButton("⤾ Back", callback_data="pass_back")]]
    await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^pass_back$"))
async def pass_back_callback(_, query: types.CallbackQuery):
    # Re-show main pass screen
    user_id = query.from_user.id
    progress = await get_user_progress(user_id)
    
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"]
    season = progress["season"]
    
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100
    
    text = (
        f"🎫 <b>Battle Pass - Season {season}</b>\n\n"
        f"{PASS_EMOJI[pass_type]} <b>Tier:</b> {pass_type.capitalize()}\n"
        f"⭐ <b>Level:</b> {level} / 50\n\n"
        f"<b>Progress to Level {level + 1}:</b>\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP"
    )
    
    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="buypass_premium")])
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    
    buttons.append([types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")])
    
    await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))

# /level command - Quick level check
@app.on_message(filters.command("level"))
async def level_cmd(_, message: types.Message):
    user_id = message.from_user.id
    progress = await get_user_progress(user_id)
    
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    
    text = (
        f"⭐ <b>Level {level}</b> / 50\n\n"
        f"{progress_bar}\n"
        f"⚡ {xp_current} / {xp_needed} XP"
    )
    
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
