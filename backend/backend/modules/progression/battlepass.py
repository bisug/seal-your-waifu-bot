from pyrogram import enums, filters, types
from pyrogram.handlers import MessageHandler, PreCheckoutQueryHandler

from backend.client import app
from backend.core.keyboard import get_webapp_button
from backend.core.pass_config import (
    MAX_PASS_LEVEL,
    PASS_MILESTONES,
    PASS_SEASON_NAME,
    PASS_TRACKS,
    calculate_pass_upgrade_price,
    get_pass_bank,
)
from backend.core.pass_payments import (
    PassPaymentError,
    create_pass_invoice,
    fulfill_pass_payment,
    validate_pass_precheckout,
)
from backend.core.progression import get_progress_bar, get_user_progress
from backend.core.utils import handle_errors
from backend.database import user_collection
from config import config


def _reward_text(track: dict, tier: str) -> str:
    reward = track.get(tier) or track["free"]
    extra = int(track.get(f"{tier}_extra_amount", 0) or 0)
    if reward["type"] == "shards":
        label = f"{reward['amount']:,} Coins"
    else:
        tier_names = {1: "Gold", 2: "Void", 3: "Rare", 4: "Legendary", 5: "Celestial"}
        label = f"{tier_names.get(int(reward.get('tier', 1)), 'Gold')} Egg"
    if extra:
        label += f" + {extra:,} Coins"
    return label


def _bank_text(bank: dict) -> str:
    shards = int(bank.get("shards", 0) or 0)
    eggs = sum(int(v) for k, v in bank.items() if str(k).startswith("eggs_t"))
    if shards <= 0 and eggs <= 0:
        return "No banked paid rewards"
    parts = []
    if shards > 0:
        parts.append(f"{shards:,} Coins")
    if eggs > 0:
        parts.append(f"{eggs} Eggs")
    return " + ".join(parts)


async def _pass_text(user_id: int) -> tuple[str, types.InlineKeyboardMarkup]:
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}}) or {}
    progress = await get_user_progress(user_id, user_data=user)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"]
    bank = get_pass_bank(user)
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    percentage = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 100

    next_milestone = next((lvl for lvl in PASS_MILESTONES if lvl > level), None)
    next_reward = ""
    if next_milestone:
        track = PASS_TRACKS[next_milestone]
        next_reward = f"\n<b>Next Reward:</b> L{next_milestone} {_reward_text(track, pass_type)}"

    text = (
        f"<b>{PASS_SEASON_NAME} Battle Pass</b>\n\n"
        f"<b>Tier:</b> {pass_type.capitalize()}\n"
        f"<b>Level:</b> {level} / {MAX_PASS_LEVEL}\n"
        f"<b>Progress:</b> {progress_bar} {percentage}%\n"
        f"<code>{xp_current} / {xp_needed}</code> XP\n"
        f"{next_reward}\n\n"
        f"<b>Paid Bank:</b> {_bank_text(bank)}"
    )

    buttons = []
    premium_price = calculate_pass_upgrade_price(pass_type, "premium")
    elite_price = calculate_pass_upgrade_price(pass_type, "elite")
    if premium_price:
        buttons.append([types.InlineKeyboardButton(f"Buy Premium - {premium_price} Stars", callback_data=f"buyask_premium:{user_id}")])
    if elite_price:
        buttons.append([types.InlineKeyboardButton(f"Buy Elite - {elite_price} Stars", callback_data=f"buyask_elite:{user_id}")])
    buttons.append([types.InlineKeyboardButton("View Rewards", callback_data=f"pass_rewards:{user_id}")])
    return text, types.InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("pass"))
@handle_errors
async def view_pass(_, message: types.Message):
    text, markup = await _pass_text(message.from_user.id)
    webapp_btn = get_webapp_button(message.chat.type == enums.ChatType.PRIVATE, path="#pass")
    buttons = markup.inline_keyboard
    if webapp_btn:
        buttons.append([webapp_btn])
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))


async def view_pass_inline(query: types.CallbackQuery):
    text, markup = await _pass_text(query.from_user.id)
    buttons = markup.inline_keyboard
    webapp_btn = get_webapp_button(query.message.chat.type == enums.ChatType.PRIVATE, path="#pass")
    if webapp_btn:
        buttons.append([webapp_btn])
    buttons.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])
    await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^buyask_(premium|elite):"))
async def buypass_ask_callback(_, query: types.CallbackQuery):
    tier = query.data.split(":")[0].split("_")[1]
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu.", show_alert=True)

    user = await user_collection.find_one({"id": {"$in": [owner_id, str(owner_id)]}}) or {}
    progress = await get_user_progress(owner_id, user_data=user)
    price = calculate_pass_upgrade_price(progress["pass_type"], tier)
    if not price:
        return await query.answer("You already have this tier or better.", show_alert=True)

    text = (
        f"<b>Confirm Stars Payment</b>\n\n"
        f"<b>{tier.capitalize()} Pass</b>\n"
        f"<b>Season:</b> {PASS_SEASON_NAME}\n"
        f"<b>Price:</b> {price} Telegram Stars"
    )
    keyboard = [[
        types.InlineKeyboardButton("Create Invoice", callback_data=f"buypass_{tier}:{owner_id}"),
        types.InlineKeyboardButton("Cancel", callback_data=f"pass_back:{owner_id}"),
    ]]
    await query.answer()
    await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(keyboard))


@app.on_callback_query(filters.regex(r"^buypass_(premium|elite):"))
async def buypass_callback(_, query: types.CallbackQuery):
    tier = query.data.split(":")[0].split("_")[1]
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu.", show_alert=True)

    try:
        invoice = await create_pass_invoice(owner_id, tier)
    except PassPaymentError as exc:
        return await query.answer(str(exc), show_alert=True)

    keyboard = [
        [types.InlineKeyboardButton(f"Pay {invoice['amount']} Stars", url=invoice["invoice_url"])],
        [types.InlineKeyboardButton("Back", callback_data=f"pass_back:{owner_id}")],
    ]
    await query.answer("Invoice ready.", show_alert=True)
    await query.message.edit_text(
        f"<b>{tier.capitalize()} Pass Invoice</b>\n\n"
        f"Pay with Telegram Stars to activate the pass. The pass activates after Telegram sends the receipt.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex(r"^pass_rewards:"))
async def view_rewards_callback(_, query: types.CallbackQuery):
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu.", show_alert=True)

    progress = await get_user_progress(owner_id)
    pass_type = progress["pass_type"]
    level = progress["level"]
    claimed = set(progress["claimed_levels"])
    text = f"<b>{PASS_SEASON_NAME} Rewards</b>\n\n<b>{pass_type.capitalize()} view</b>\n\n"

    for milestone in PASS_MILESTONES:
        track = PASS_TRACKS[milestone]
        status = "Claimed" if milestone in claimed else "Ready" if level >= milestone else "Locked"
        text += f"<b>L{milestone}</b> {status}: {_reward_text(track, pass_type)}\n"

    buttons = [[types.InlineKeyboardButton("Back", callback_data=f"pass_back:{owner_id}")]]
    await query.answer()
    await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=types.InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^pass_back:"))
async def pass_back_callback(_, query: types.CallbackQuery):
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu.", show_alert=True)
    await query.answer()
    await view_pass_inline(query)


@app.on_message(filters.command("level"))
@handle_errors
async def level_cmd(_, message: types.Message):
    progress = await get_user_progress(message.from_user.id)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    progress_bar = get_progress_bar(xp_current, xp_needed, 10)
    await message.reply_text(
        f"<b>Level {level}</b> / {MAX_PASS_LEVEL}\n\n"
        f"{progress_bar}\n"
        f"<code>{xp_current} / {xp_needed}</code> XP",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("paysupport"))
async def pay_support_cmd(_, message: types.Message):
    await message.reply_text(
        f"<b>Payment Support</b>\n\n"
        f"For Battle Pass payment help, contact @{config.SUPPORT_CHAT} and include your Telegram ID: "
        f"<code>{message.from_user.id}</code>.",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("terms"))
async def terms_cmd(_, message: types.Message):
    await message.reply_text(
        "<b>Digital Purchase Terms</b>\n\n"
        "Battle Pass purchases are digital goods delivered inside this Telegram bot. "
        "Payments are processed with Telegram Stars. Refund requests are handled through /paysupport.",
        parse_mode=enums.ParseMode.HTML,
    )


async def pass_precheckout_handler(_, pre_checkout_query):
    ok, error = await validate_pass_precheckout(pre_checkout_query)
    await pre_checkout_query.answer(ok=ok, error_message=error)


async def pass_successful_payment_handler(_, message: types.Message):
    result = await fulfill_pass_payment(message.from_user.id, message.successful_payment)
    if result.get("status") in {"fulfilled", "already_fulfilled"}:
        await message.reply_text(
            f"<b>{result.get('tier', 'Pass').capitalize()} Pass activated.</b>\n\n"
            "Open /pass to view your rewards.",
            parse_mode=enums.ParseMode.HTML,
        )


def load_handlers(bot):
    if bot.name != "MainBot":
        return
    bot.add_handler(PreCheckoutQueryHandler(pass_precheckout_handler), group=0)
    bot.add_handler(MessageHandler(pass_successful_payment_handler, filters.successful_payment), group=0)
