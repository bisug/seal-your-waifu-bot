from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import LOGGER
from Grabber.core.user import get_user_data, update_user

# Global trade registers
pending_trades = {}

@app.on_message(filters.command("trade") & filters.group)
async def trade_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to trade!")

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        return await message.reply_text("⚠️ No self-trading!")

    if len(message.command) != 3:
        return await message.reply_text("❌ Use: `/trade <your_char_id> <their_char_id>`")

    s_char_id, r_char_id = message.command[1], message.command[2]

    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)

    if not sender or not receiver:
        return await message.reply_text("❌ Database error.")

    # Business logic: Ownership check
    s_char = next((c for c in sender.get('characters', []) if str(c.get('id')) == s_char_id), None)
    r_char = next((c for c in receiver.get('characters', []) if str(c.get('id')) == r_char_id), None)

    if not s_char:
        return await message.reply_text("❌ You don't own that character.")
    if not r_char:
        return await message.reply_text("❌ They don't own that character.")

    trade_id = f"{sender_id}_{receiver_id}"
    pending_trades[trade_id] = (s_char, r_char)

    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("✅ Confirm", callback_data=f"tr_c:{trade_id}"),
         types.InlineKeyboardButton("❌ Cancel", callback_data=f"tr_x:{trade_id}")]
    ])

    await message.reply_to_message.reply_text(
        f"🤝 {message.reply_to_message.from_user.mention}, accept trade?\n\n"
        f"📤 **Give:** {s_char['name']}\n"
        f"📥 **Take:** {r_char['name']}",
        reply_markup=markup
    )

@app.on_callback_query(filters.regex(r"^tr_(c|x):"))
async def trade_callback_handler(_, query: types.CallbackQuery):
    action, trade_id = query.data.split(":")
    trade_info = pending_trades.get(trade_id)

    if not trade_info:
        return await query.answer("❌ Trade expired.", show_alert=True)

    sender_id, receiver_id = map(int, trade_id.split("_"))

    if action == "x":
        if query.from_user.id not in [sender_id, receiver_id]:
            return await query.answer("❌ Not yours!")
        pending_trades.pop(trade_id, None)
        return await query.message.edit_text("❌ Trade canceled.")

    if query.from_user.id != receiver_id:
        return await query.answer("❌ This is for the receiver to accept!", show_alert=True)

    s_char, r_char = trade_info
    
    # Atomic-like exchange with checks
    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)
    
    if not any(c['id'] == s_char['id'] for c in sender['characters']) or \
       not any(c['id'] == r_char['id'] for c in receiver['characters']):
        return await query.message.edit_text("❌ One of the characters is no longer available.")

    await update_user(sender_id, {
        "$pull": {"characters": {"id": s_char['id']}},
        "$push": {"characters": r_char}
    })
    await update_user(receiver_id, {
        "$pull": {"characters": {"id": r_char['id']}},
        "$push": {"characters": s_char}
    })

    pending_trades.pop(trade_id, None)
    await query.message.edit_text(f"✅ Trade successful between {sender_id} and {receiver_id}!")
    LOGGER.info(f"Trade complete: {sender_id} <-> {receiver_id}")
