from pyrogram import enums, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from config import config
from Grabber import WEB_APP_URL, app, user_collection
from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
from Grabber.core.progression import (LEVEL_REWARDS, get_progress_bar,
                                      get_user_progress)

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
    """View the user's current Battle Pass progress and tier."""
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
        f"🎫 <b>Battle Pass - Season {season}</b>\n\n"
        f"{PASS_EMOJI[pass_type]} <b>Tier:</b> {pass_type.capitalize()}\n"
        f"⭐ <b>Level:</b> {level} / 50\n\n"
        f"<b>Progress to Level {level + 1}:</b>\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ <code>{xp_current} / {xp_needed}</code> XP\n\n"
    )

    if next_milestone:
        text += f"🎯 <b>Next Milestone:</b> Level {next_milestone}\n"


    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("Upgrade to Premium", callback_data=f"buyask_premium:{user_id}", style=ButtonStyle.SUCCESS)])
        buttons.append([types.InlineKeyboardButton("Upgrade to Elite", callback_data=f"buyask_elite:{user_id}", style=ButtonStyle.SUCCESS)])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("Upgrade to Elite", callback_data=f"buyask_elite:{user_id}", style=ButtonStyle.SUCCESS)])

    buttons.append([types.InlineKeyboardButton("View Rewards", callback_data=f"pass_rewards:{user_id}", style=ButtonStyle.PRIMARY)])
    
    webapp_btn = get_webapp_button(message.chat.type == enums.ChatType.PRIVATE)
    if webapp_btn:
        buttons.append([webapp_btn])
        
    markup = types.InlineKeyboardMarkup(buttons)
    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def view_pass_inline(query: types.CallbackQuery):
    """Display the Battle Pass menu as an inline callback response."""
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
        f"⚡ <code>{xp_current} / {xp_needed}</code> XP\n\n"
    )

    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("Upgrade to Premium", callback_data=f"buyask_premium:{user_id}", style=ButtonStyle.SUCCESS)])
        buttons.append([types.InlineKeyboardButton("Upgrade to Elite", callback_data=f"buyask_elite:{user_id}", style=ButtonStyle.SUCCESS)])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("Upgrade to Elite", callback_data=f"buyask_elite:{user_id}", style=ButtonStyle.SUCCESS)])

    buttons.append([types.InlineKeyboardButton("View Rewards", callback_data=f"pass_rewards:{user_id}", style=ButtonStyle.PRIMARY)])
    
    webapp_btn = get_webapp_button(query.message.chat.type == enums.ChatType.PRIVATE)
    if webapp_btn:
        buttons.append([webapp_btn])
        
    buttons.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])

    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^buyask_(premium|elite):"))
async def buypass_ask_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    tier = data[0].split("_")[1]
    owner_id = int(data[1])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    await query.answer()  # Dismiss spinner instantly
    price = PASS_PRICES[tier]
    text = f"⚠️ <b>Confirm Upgrade</b>\n\nUpgrade to <b>{tier.capitalize()} Pass</b> for <b>{price} ⧫</b>?"
    keyboard = [[
        types.InlineKeyboardButton("Confirm Upgrade", callback_data=f"buypass_{tier}:{owner_id}", style=enums.ButtonStyle.SUCCESS),
        types.InlineKeyboardButton("Cancel", callback_data=f"pass_back:{owner_id}", style=enums.ButtonStyle.DANGER)
    ]]
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(keyboard))


@app.on_callback_query(filters.regex(r"^buypass_(premium|elite):"))
async def buypass_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    tier = data[0].split("_")[1]
    owner_id = int(data[1])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    user_id = query.from_user.id
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
        f"🎫 <b>Battle Pass - Season {season}</b>\n\n"
        f"{PASS_EMOJI[tier]} <b>Tier:</b> {tier.capitalize()}\n"
        f"⭐ <b>Level:</b> {level} / 50\n\n"
        f"<b>Progress to Level {level + 1}:</b>\n"
        f"{progress_bar} {percentage}%\n"
        f"⚡ <code>{xp_current} / {xp_needed}</code> XP\n\n"
        f"✨ <i>Upgraded rewards active!</i>"
    )

    buttons = [[types.InlineKeyboardButton("View Rewards", callback_data=f"pass_rewards:{user_id}", style=enums.ButtonStyle.PRIMARY)]]
    if tier == "premium":
        buttons.insert(0, [types.InlineKeyboardButton("Upgrade to Elite", callback_data=f"buypass_elite:{user_id}", style=enums.ButtonStyle.SUCCESS)])

    try:
        await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))
    except:
        pass


@app.on_callback_query(filters.regex(r"^pass_rewards:"))
async def view_rewards_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    owner_id = int(data[1])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    await query.answer()  # Dismiss spinner instantly
    user_id = query.from_user.id  # Must be declared before use
    progress = await get_user_progress(user_id)

    pass_type = progress["pass_type"]
    level = progress["level"]
    claimed = set(progress["claimed_levels"])

    text = f"🎁 <b>Battle Pass Rewards</b>\n\n{PASS_EMOJI[pass_type]} <b>{pass_type.capitalize()} Tier</b>\n\n"

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

        text += f"{status} <b>Level {milestone}:</b> {reward_text}\n"

    buttons = [[types.InlineKeyboardButton("Back", callback_data=f"pass_back:{user_id}")]]
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^pass_back:"))
async def pass_back_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    owner_id = int(data[1])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    await query.answer()  # Dismiss spinner instantly
    user_id = query.from_user.id  # Must be declared before use
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
        f"⚡ <code>{xp_current} / {xp_needed}</code> XP"
    )

    buttons = []
    if pass_type == "free":
        buttons.append([types.InlineKeyboardButton("⭐ Upgrade to Premium", callback_data=f"buypass_premium:{user_id}", style=enums.ButtonStyle.SUCCESS)])
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data=f"buypass_elite:{user_id}", style=enums.ButtonStyle.SUCCESS)])
    elif pass_type == "premium":
        buttons.append([types.InlineKeyboardButton("💎 Upgrade to Elite", callback_data=f"buypass_elite:{user_id}", style=enums.ButtonStyle.SUCCESS)])

    buttons.append([types.InlineKeyboardButton("View Rewards", callback_data=f"pass_rewards:{user_id}", style=enums.ButtonStyle.PRIMARY)])

    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))


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
        f"⚡ <code>{xp_current} / {xp_needed}</code> XP"
    )

    await message.reply_text(text, parse_mode=ParseMode.HTML)
