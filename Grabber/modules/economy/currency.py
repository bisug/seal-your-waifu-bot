from pyrogram import enums, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from Grabber import app
from Grabber.core.utils import html_escape
from Grabber.database import user_collection


@app.on_message(filters.command("exchange"))
async def exchange_command(_, message: types.Message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text(
            "💱 <b>Shards → Zenith Exchange</b>\n\n"
            "<b>Usage:</b> <code>/exchange &lt;amount&gt;</code>\n"
            "<b>Example:</b> <code>/exchange 50000</code>\n\n"
            "<b>Rate:</b> 10,000 ⬪ = 1 ⧫\n"
            "<b>Minimum:</b> 10,000 Shards",
            parse_mode=ParseMode.HTML
        )

    try:
        shards_amount = int(message.command[1].replace(",", ""))
    except ValueError:
        return await message.reply_text("❌ Invalid amount. Please enter a number.")

    if shards_amount < 10000:
        return await message.reply_text(f"❌ Minimum exchange is 10,000 ⬪ Shards (= 1 ⧫ Zenith).")

    if shards_amount % 10000 != 0:
        return await message.reply_text(f"❌ Amount must be divisible by 10,000 ⬪.")

    user = await user_collection.find_one({"id": user_id})
    current_shards = user.get("balance", 0) if user else 0

    if current_shards < shards_amount:
        return await message.reply_text(
            f"❌ Insufficient Shards!\n\n"
            f"You have: {current_shards:,} ⬪\n"
            f"Need: {shards_amount:,} ⬪"
        )

    zenith_amount = shards_amount // 10000


    new_shards = current_shards - shards_amount
    current_zenith = user.get("zenith", 0) if user else 0
    new_zenith = current_zenith + zenith_amount


    confirmation_text = (
        f"💱 <b>Exchange Confirmation</b>\n\n"
        f"<b>Converting:</b> <code>{shards_amount:,}</code> ⬪ → <code>{zenith_amount:,}</code> ⧫\n\n"
        f"<b>Current Balance:</b>\n"
        f"Shards: <code>{current_shards:,}</code> ⬪\n"
        f"Zenith: <code>{current_zenith:,}</code> ⧫\n\n"
        f"<b>New Balance:</b>\n"
        f"Shards: <code>{new_shards:,}</code> ⬪\n"
        f"Zenith: <code>{new_zenith:,}</code> ⧫\n\n"
        f"<i>Proceed with exchange?</i>"
    )

    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"exchange_confirm_{shards_amount}_{user_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"exchange_cancel_{user_id}")
        ]
    ]

    await message.reply_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )


@app.on_callback_query(filters.regex(r"^exchange_confirm_(\d+)_(\d+)$"))
async def exchange_confirm_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    shards_amount = int(data[2])
    owner_id = int(data[3])
    user_id = query.from_user.id

    if owner_id and user_id != owner_id:
        return await query.answer("❌ This is not your exchange!", show_alert=True)

    user = await user_collection.find_one({"id": user_id})
    current_shards = user.get("balance", 0) if user else 0


    if current_shards < shards_amount:
        await query.answer("❌ Insufficient Shards!", show_alert=True)
        return

    zenith_amount = shards_amount // 10000


    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {
                "balance": -shards_amount,
                "zenith": zenith_amount
            }
        },
        upsert=True
    )


    new_shards = current_shards - shards_amount
    current_zenith = user.get("zenith", 0) if user else 0
    new_zenith = current_zenith + zenith_amount

    await query.message.edit_text(
        f"✅ <b>Exchange Successful!</b>\n\n"
        f"Converted: <code>{shards_amount:,}</code> ⬪ → <code>{zenith_amount:,}</code> ⧫\n\n"
        f"<b>Your New Balance:</b>\n"
        f"Shards: <code>{new_shards:,}</code> ⬪\n"
        f"Zenith: <code>{new_zenith:,}</code> ⧫",
        parse_mode=ParseMode.HTML
    )
    await query.answer("Exchange completed!")


@app.on_callback_query(filters.regex(r"^exchange_cancel_(\d+)$"))
async def exchange_cancel_callback(_, query: types.CallbackQuery):
    owner_id = int(query.data.split("_")[2])
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your exchange!", show_alert=True)
    await query.message.edit_text(
        "❌ <b>Exchange Cancelled</b>\n\n"
        "Your balance remains unchanged.",
        parse_mode=ParseMode.HTML
    )
    await query.answer("Cancelled")
