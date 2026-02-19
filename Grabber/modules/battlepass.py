from pyrogram import filters, types, enums
from Grabber import user_collection, app
from Grabber.core.progression import get_user_progress, get_progress_bar, LEVEL_REWARDS

                           
PASS_PRICES = {
    "premium": 25,
    "elite": 60
}

                  
PASS_EMOJI = {
    "free": "🆓",
    "premium": "⭐",
    "elite": "💎"
}

                                                  
@app.on_message(filters.command("pass"))
async def view_pass(_, message: types.Message):
    user_id = message.from_user.id
    progress = await get_user_progress(user_id)
    
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"]
    season = progress["season"]
    
                         
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100
    
                    
    next_milestone = None
    for milestone_level in sorted(LEVEL_REWARDS.keys()):
        if milestone_level > level:
            next_milestone = milestone_level
            break
    
    text = (
        f"🎫 **Battle Pass - Season {season}**\n\n"
        f"{PASS_EMOJI[pass_type]} **Tier:** {pass_type.capitalize()}\n"
        f"⭐ **Level:** {level} / 50\n\n"
        f"**Progress to Level {level + 1}:**\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP\n\n"
    )
    
    if next_milestone:
        text += f"🎯 **Next Milestone:** Level {next_milestone}\n"
    
                                       
    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="buypass_premium")])
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    
    buttons.append([types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")])
    
    markup = types.InlineKeyboardMarkup(buttons)
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=markup)

                            
async def view_pass_inline(query: types.CallbackQuery):
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
        f"🎫 **Battle Pass - Season {season}**\n\n"
        f"{PASS_EMOJI[pass_type]} **Tier:** {pass_type.capitalize()}\n"
        f"⭐ **Level:** {level} / 50\n\n"
        f"**Progress to Level {level + 1}:**\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP\n\n"
    )
    
    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="buyask_premium")])
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buyask_elite")])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buyask_elite")])
    
    buttons.append([types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")])
    buttons.append([types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")])
    
    await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=types.InlineKeyboardMarkup(buttons))

                                  
@app.on_callback_query(filters.regex(r"^buyask_(premium|elite)$"))
async def buypass_ask_callback(_, query: types.CallbackQuery):
    tier = query.data.split("_")[1]
    price = PASS_PRICES[tier]
    text = f"⚠️ **Confirm Upgrade**\n\nUpgrade to **{tier.capitalize()} Pass** for **{price} ⧫**?"
    keyboard = [[
        types.InlineKeyboardButton("Confirm ✅", callback_data=f"buypass_{tier}"),
        types.InlineKeyboardButton("Cancel ❌", callback_data="hub_pass")
    ]]
    await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=types.InlineKeyboardMarkup(keyboard))

                                            
@app.on_callback_query(filters.regex(r"^buypass_(premium|elite)$"))
async def buypass_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    tier = query.data.split("_")[1]
    price = PASS_PRICES[tier]
    
    user = await user_collection.find_one({"id": user_id})
    
    if not user:
        return await query.answer("❌ No profile found!", show_alert=True)
    
    current_tier = user.get("pass_type", "free")
    
                                      
    tiers_order = ["free", "premium", "elite"]
    if tiers_order.index(current_tier) >= tiers_order.index(tier):
        return await query.answer(f"✅ You already have {current_tier.capitalize()} or better!", show_alert=True)
    
                            
    user_zenith = user.get("zenith", 0)
    if user_zenith < price:
        return await query.answer(f"❌ Insufficient Zenith! Need {price} ⧫.", show_alert=True)
    
              
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"pass_type": tier},
            "$inc": {"zenith": -price}
        }
    )
    
    await query.answer(f"🎉 {tier.capitalize()} Pass activated!", show_alert=True)
    
                     
    progress = await get_user_progress(user_id)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    season = progress["season"]
    
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100
    
    text = (
        f"🎫 **Battle Pass - Season {season}**\n\n"
        f"{PASS_EMOJI[tier]} **Tier:** {tier.capitalize()}\n"
        f"⭐ **Level:** {level} / 50\n\n"
        f"**Progress to Level {level + 1}:**\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ {xp_current} / {xp_needed} XP\n\n"
        f"✨ _Upgraded rewards active!_"
    )
    
    buttons = [[types.InlineKeyboardButton("🎁 View Rewards", callback_data="pass_rewards")]]
    if tier == "premium":
        buttons.insert(0, [types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data="buypass_elite")])
    
    try:
        await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=types.InlineKeyboardMarkup(buttons))
    except:
        pass

                        
@app.on_callback_query(filters.regex(r"^pass_rewards$"))
async def view_rewards_callback(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    progress = await get_user_progress(user_id)
    
    pass_type = progress["pass_type"]
    level = progress["level"]
    claimed = set(progress["claimed_levels"])
    
    text = f"🎁 **Battle Pass Rewards**\n\n{PASS_EMOJI[pass_type]} **{pass_type.capitalize()} Tier**\n\n"
    
    for milestone in sorted(LEVEL_REWARDS.keys()):
        reward = LEVEL_REWARDS[milestone].get(pass_type, "None")
        
                       
        if isinstance(reward, int):
            reward_text = f"{reward:,} ⬪"
        elif isinstance(reward, str) and reward.startswith("egg_"):
            tier_name = reward.split("_")[1].capitalize()
            reward_text = f"{tier_name} Egg"
        else:
            reward_text = "Special Reward"
        
                
        if milestone in claimed:
            status = "✅"
        elif level >= milestone:
            status = "🎁"
        else:
            status = "🔒"
        
        text += f"{status} **Level {milestone}:** {reward_text}\n"
    
    buttons = [[types.InlineKeyboardButton("⤾ Back", callback_data="pass_back")]]
    await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=types.InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^pass_back$"))
async def pass_back_callback(_, query: types.CallbackQuery):
                              
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
        f"🎫 **Battle Pass - Season {season}**\n\n"
        f"{PASS_EMOJI[pass_type]} **Tier:** {pass_type.capitalize()}\n"
        f"⭐ **Level:** {level} / 50\n\n"
        f"**Progress to Level {level + 1}:**\n"
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
    
    await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=types.InlineKeyboardMarkup(buttons))

                                    
@app.on_message(filters.command("level"))
async def level_cmd(_, message: types.Message):
    user_id = message.from_user.id
    progress = await get_user_progress(user_id)
    
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    
    text = (
        f"⭐ **Level {level}** / 50\n\n"
        f"{progress_bar}\n"
        f"⚡ {xp_current} / {xp_needed} XP"
    )
    
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)
