from pyrogram import enums, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from Grabber import app
from Grabber.core.user import get_user_filter, get_user_id
from Grabber.core.cache import invalidate_user_cache
from Grabber.database import user_collection


@app.on_message(filters.command("zenith"))
async def zenith_command(_, message: types.Message):
    """Convert Shards to Zenith."""
    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Shards → Zenith Exchange</b>\n\n"
            "<b>Usage:</b> <code>/zenith &lt;amount&gt;</code>\n"
            "<b>Example:</b> <code>/zenith 50000</code>\n\n"
            "<b>Rate:</b> 10,000 ⬪ = 1 ⧫\n"
            "<b>Minimum:</b> 10,000 Shards",
            parse_mode=ParseMode.HTML
        )

    try:
        shards_amount = int(message.command[1].replace(",", ""))
    except ValueError:
        return await message.reply_text("Invalid amount. Please enter a number.")

    if shards_amount < 10000:
        return await message.reply_text("Minimum exchange is 10,000 ⬪ Shards.")

    if shards_amount % 10000 != 0:
        return await message.reply_text("Amount must be divisible by 10,000 ⬪.")

    user = await user_collection.find_one(get_user_filter(user_id))
    current_shards = user.get("balance", 0) if user else 0

    if current_shards < shards_amount:
        return await message.reply_text(
            f"Insufficient Shards!\n\n"
            f"You have: {current_shards:,} ⬪\n"
            f"Need: {shards_amount:,} ⬪"
        )

    zenith_amount = shards_amount // 10000
    
    buttons = [
        [
            types.InlineKeyboardButton("Confirm", callback_data=f"conv_s_{shards_amount}_{user_id}"),
            types.InlineKeyboardButton("Cancel", callback_data=f"conv_cancel_{user_id}")
        ]
    ]

    await message.reply_text(
        f"<b>Exchange Confirmation</b>\n\n"
        f"<b>Converting:</b> <code>{shards_amount:,}</code> ⬪ → <b>{zenith_amount:,}</b> ⧫\n\n"
        f"<i>Proceed?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )


@app.on_message(filters.command("shard"))
async def shard_command(_, message: types.Message):
    """Convert Zenith to Shards."""
    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Zenith → Shards Exchange</b>\n\n"
            "<b>Usage:</b> <code>/shard &lt;amount&gt;</code>\n"
            "<b>Example:</b> <code>/shard 5</code>\n\n"
            "<b>Rate:</b> 1 ⧫ = 10,000 ⬪\n"
            "<b>Minimum:</b> 1 Zenith",
            parse_mode=ParseMode.HTML
        )

    try:
        zenith_amount = int(message.command[1].replace(",", ""))
    except ValueError:
        return await message.reply_text("Invalid amount. Please enter a number.")

    if zenith_amount < 1:
        return await message.reply_text("Minimum exchange is 1 ⧫ Zenith.")

    user = await user_collection.find_one(get_user_filter(user_id))
    current_zenith = user.get("zenith", 0) if user else 0

    if current_zenith < zenith_amount:
        return await message.reply_text(
            f"Insufficient Zenith!\n\n"
            f"You have: {current_zenith:,} ⧫\n"
            f"Need: {zenith_amount:,} ⧫"
        )

    shards_amount = zenith_amount * 10000
    
    buttons = [
        [
            types.InlineKeyboardButton("Confirm", callback_data=f"conv_z_{zenith_amount}_{user_id}"),
            types.InlineKeyboardButton("Cancel", callback_data=f"conv_cancel_{user_id}")
        ]
    ]

    await message.reply_text(
        f"<b>Exchange Confirmation</b>\n\n"
        f"<b>Converting:</b> <code>{zenith_amount:,}</code> ⧫ → <b>{shards_amount:,}</b> ⬪\n\n"
        f"<i>Proceed?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )


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
        zenith_to_add = amount // 10000
        
        if user.get("balance", 0) < shards_to_deduct:
            return await query.answer("Insufficient Shards!", show_alert=True)
            
        update_query = {
            "$inc": {
                "balance": -shards_to_deduct,
                "zenith": zenith_to_add
            }
        }
        success_text = f"Converted: <code>{shards_to_deduct:,}</code> ⬪ → <b>{zenith_to_add:,}</b> ⧫"
    else:
        # Zenith to Shards
        zenith_to_deduct = amount
        shards_to_add = amount * 10000
        
        if user.get("zenith", 0) < zenith_to_deduct:
            return await query.answer("Insufficient Zenith!", show_alert=True)
            
        update_query = {
            "$inc": {
                "balance": shards_to_add,
                "zenith": -zenith_to_deduct
            }
        }
        success_text = f"Converted: <code>{zenith_to_deduct:,}</code> ⧫ → <b>{shards_to_add:,}</b> ⬪"

    # Atomic update
    await user_collection.update_one({"id": get_user_id(user_id)}, update_query)
    await invalidate_user_cache(user_id)

    await query.message.edit_text(
        f"<b>Exchange Successful!</b>\n\n"
        f"{success_text}\n\n"
        f"<i>Your balance has been updated.</i>",
        parse_mode=ParseMode.HTML
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
        parse_mode=ParseMode.HTML
    )
    await query.answer("Cancelled")
