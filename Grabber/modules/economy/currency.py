from pyrogram import enums, filters, types

from Grabber import app
from Grabber.core.cache import invalidate_user_cache, sync_user_to_redis
from Grabber.core.keyboard import get_webapp_button
from Grabber.core.user import get_user_filter
from Grabber.core.utils import handle_errors
from Grabber.database import user_collection

EXCHANGE_RATE = 10_000


def _parse_amount(raw: str) -> int | None:
    try:
        amount = int(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


async def _send_shards_to_zenith_confirmation(message: types.Message, shards_amount: int):
    user_id = message.from_user.id
    if shards_amount < EXCHANGE_RATE:
        return await message.reply_text(f"Minimum exchange is {EXCHANGE_RATE:,} Shards.")
    if shards_amount % EXCHANGE_RATE != 0:
        return await message.reply_text(f"Amount must be divisible by {EXCHANGE_RATE:,} Shards.")

    user = await user_collection.find_one(get_user_filter(user_id))
    current_shards = user.get("balance", 0) if user else 0
    if current_shards < shards_amount:
        return await message.reply_text(
            f"Insufficient Shards!\n\n"
            f"You have: {current_shards:,}\n"
            f"Need: {shards_amount:,}"
        )

    zenith_amount = shards_amount // EXCHANGE_RATE
    buttons = [[
        types.InlineKeyboardButton("Confirm", callback_data=f"conv_s_{shards_amount}_{user_id}"),
        types.InlineKeyboardButton("Cancel", callback_data=f"conv_cancel_{user_id}"),
    ]]
    await message.reply_text(
        f"<b>Exchange Confirmation</b>\n\n"
        f"<b>Converting:</b> <code>{shards_amount:,}</code> Shards to <b>{zenith_amount:,}</b> Zenith\n\n"
        f"<i>Proceed?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
    )


async def _send_zenith_to_shards_confirmation(message: types.Message, zenith_amount: int):
    user_id = message.from_user.id
    if zenith_amount < 1:
        return await message.reply_text("Minimum exchange is 1 Zenith.")

    user = await user_collection.find_one(get_user_filter(user_id))
    current_zenith = user.get("zenith", 0) if user else 0
    if current_zenith < zenith_amount:
        return await message.reply_text(
            f"Insufficient Zenith!\n\n"
            f"You have: {current_zenith:,}\n"
            f"Need: {zenith_amount:,}"
        )

    shards_amount = zenith_amount * EXCHANGE_RATE
    buttons = [[
        types.InlineKeyboardButton("Confirm", callback_data=f"conv_z_{zenith_amount}_{user_id}"),
        types.InlineKeyboardButton("Cancel", callback_data=f"conv_cancel_{user_id}"),
    ]]
    await message.reply_text(
        f"<b>Exchange Confirmation</b>\n\n"
        f"<b>Converting:</b> <code>{zenith_amount:,}</code> Zenith to <b>{shards_amount:,}</b> Shards\n\n"
        f"<i>Proceed?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("exchange"))
@handle_errors
async def exchange_command(_, message: types.Message):
    """Show exchange help or convert using /exchange shards|zenith <amount>."""
    user_id = message.from_user.id
    user = await user_collection.find_one(get_user_filter(user_id)) or {}

    if len(message.command) >= 3:
        direction = message.command[1].lower()
        amount = _parse_amount(message.command[2])
        if amount is None:
            return await message.reply_text("Invalid amount. Please enter a number.")
        if direction in {"shards", "shard", "s", "tozenith"}:
            return await _send_shards_to_zenith_confirmation(message, amount)
        if direction in {"zenith", "z", "toshards"}:
            return await _send_zenith_to_shards_confirmation(message, amount)

    if len(message.command) == 2:
        amount = _parse_amount(message.command[1])
        if amount is not None:
            return await _send_shards_to_zenith_confirmation(message, amount)

    buttons = []
    webapp_btn = get_webapp_button(message.chat.type == enums.ChatType.PRIVATE, path="#shop")
    if webapp_btn:
        buttons.append([webapp_btn])

    await message.reply_text(
        "<b>Currency Exchange</b>\n\n"
        f"<b>Your Shards:</b> <code>{int(user.get('balance', 0) or 0):,}</code>\n"
        f"<b>Your Zenith:</b> <code>{int(user.get('zenith', 0) or 0):,}</code>\n\n"
        f"<b>Rate:</b> {EXCHANGE_RATE:,} Shards = 1 Zenith\n\n"
        "<b>Commands:</b>\n"
        "<code>/exchange 10000</code> - Shards to Zenith\n"
        "<code>/zenith 10000</code> - Shards to Zenith\n"
        "<code>/shard 1</code> - Zenith to Shards",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(buttons) if buttons else None,
    )


@app.on_message(filters.command("zenith"))
@handle_errors
async def zenith_command(_, message: types.Message):
    """Convert Shards to Zenith."""
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Shards → Zenith Exchange</b>\n\n"
            "<b>Usage:</b> <code>/zenith &lt;amount&gt;</code>\n"
            "<b>Example:</b> <code>/zenith 50000</code>\n\n"
            "<b>Rate:</b> 10,000 ⬪ = 1 ⧫\n"
            "<b>Minimum:</b> 10,000 Shards",
            parse_mode=enums.ParseMode.HTML
        )
    shards_amount = _parse_amount(message.command[1])
    if shards_amount is None:
        return await message.reply_text("Invalid amount. Please enter a number.")
    await _send_shards_to_zenith_confirmation(message, shards_amount)


@app.on_message(filters.command("shard"))
@handle_errors
async def shard_command(_, message: types.Message):
    """Convert Zenith to Shards."""
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Zenith → Shards Exchange</b>\n\n"
            "<b>Usage:</b> <code>/shard &lt;amount&gt;</code>\n"
            "<b>Example:</b> <code>/shard 5</code>\n\n"
            "<b>Rate:</b> 1 ⧫ = 10,000 ⬪\n"
            "<b>Minimum:</b> 1 Zenith",
            parse_mode=enums.ParseMode.HTML
        )
    zenith_amount = _parse_amount(message.command[1])
    if zenith_amount is None:
        return await message.reply_text("Invalid amount. Please enter a number.")
    await _send_zenith_to_shards_confirmation(message, zenith_amount)


@app.on_callback_query(filters.regex(r"^conv_([sz])_(\d+)_(\d+)$"))
async def conversion_confirm_callback(_, query: types.CallbackQuery):
    mode = query.matches[0].group(1)
    amount = int(query.matches[0].group(2))
    owner_id = int(query.matches[0].group(3))
    user_id = query.from_user.id
    if user_id != owner_id:
        return await query.answer("This is not your exchange!", show_alert=True)
    user = await user_collection.find_one(get_user_filter(user_id))
    if not user:
        return await query.answer("User profile not found!", show_alert=True)
    if mode == "s":
        # Shards to Zenith
        shards_to_deduct = amount
        zenith_to_add = amount // EXCHANGE_RATE
        if user.get("balance", 0) < shards_to_deduct:
            return await query.answer("Insufficient Shards!", show_alert=True)
        update_filter = get_user_filter(user_id)
        update_filter["balance"] = {"$gte": shards_to_deduct}
        update_query = {
            "$inc": {
                "balance": -shards_to_deduct,
                "zenith": zenith_to_add,
                "version": 1
            }
        }
        success_text = f"Converted: <code>{shards_to_deduct:,}</code> Shards to <b>{zenith_to_add:,}</b> Zenith"
    else:
        # Zenith to Shards
        zenith_to_deduct = amount
        shards_to_add = amount * EXCHANGE_RATE
        if user.get("zenith", 0) < zenith_to_deduct:
            return await query.answer("Insufficient Zenith!", show_alert=True)
        update_filter = get_user_filter(user_id)
        update_filter["zenith"] = {"$gte": zenith_to_deduct}
        update_query = {
            "$inc": {
                "balance": shards_to_add,
                "zenith": -zenith_to_deduct,
                "version": 1
            }
        }
        success_text = f"Converted: <code>{zenith_to_deduct:,}</code> Zenith to <b>{shards_to_add:,}</b> Shards"
    # Atomic update
    result = await user_collection.update_one(update_filter, update_query)
    if result.modified_count == 0:
        return await query.answer("Balance changed. Please run /exchange again.", show_alert=True)
    await invalidate_user_cache(user_id)
    await sync_user_to_redis(user_id)
    await query.message.edit_text(
        f"<b>Exchange Successful!</b>\n\n"
        f"{success_text}\n\n"
        f"<i>Your balance has been updated.</i>",
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer("Exchange completed!")
@app.on_callback_query(filters.regex(r"^conv_cancel_(\d+)$"))
async def conversion_cancel_callback(_, query: types.CallbackQuery):
    owner_id = int(query.matches[0].group(1))
    if query.from_user.id != owner_id:
        return await query.answer("This is not your exchange!", show_alert=True)
    await query.message.edit_text(
        "<b>Exchange Cancelled</b>\n\n"
        "Your balance remains unchanged.",
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer("Cancelled")
