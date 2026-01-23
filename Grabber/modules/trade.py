from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import LOGGER
from Grabber.core.user import get_user_data, update_user
from Grabber.core.sessions import create_session, get_session, delete_session

@app.on_message(filters.command("trade") & filters.group)
async def trade_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to trade!")

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        return await message.reply_text("⚠️ No self-trading!")

    if len(message.command) != 3:
        return await message.reply_text("❌ Usage: <code>/trade &lt;your_char_id&gt; &lt;their_char_id&gt;</code>", parse_mode=enums.ParseMode.HTML)

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

    # Store trade in MongoDB
    trade_id = f"tr_{sender_id}_{receiver_id}"
    await create_session(trade_id, {"s_char": s_char, "r_char": r_char, "s_id": sender_id, "r_id": receiver_id})

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
    
    # Fetch from MongoDB
    trade_info = await get_session(trade_id)

    if not trade_info:
        return await query.answer("❌ Trade expired or handled.", show_alert=True)

    sender_id, receiver_id = trade_info["s_id"], trade_info["r_id"]

    if action == "x":
        if query.from_user.id not in [sender_id, receiver_id]:
            return await query.answer("❌ Not yours!", show_alert=True)
        await delete_session(trade_id)
        try:
            await query.message.edit_text("❌ Trade canceled.")
        except errors.MessageNotModified:
            pass
        return

    if query.from_user.id != receiver_id:
        return await query.answer("❌ This is for the receiver to accept!", show_alert=True)

    s_char, r_char = trade_info["s_char"], trade_info["r_char"]
    
    # Final ownership check before exchange
    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)
    
    if not any(c['id'] == s_char['id'] for c in sender['characters']) or \
       not any(c['id'] == r_char['id'] for c in receiver['characters']):
        await delete_session(trade_id)
        return await query.message.edit_text("❌ One of the characters is no longer available.")

    # Instant Feedback
    await query.answer("Processing trade...", cache_time=1)

    # Remove session from DB immediately
    await delete_session(trade_id)

    # Perform exchange
    await update_user(sender_id, {
        "$pull": {"characters": {"id": s_char['id']}},
        "$push": {"characters": r_char}
    })
    await update_user(receiver_id, {
        "$pull": {"characters": {"id": r_char['id']}},
        "$push": {"characters": s_char}
    })

    await query.message.edit_text(f"✅ Trade successful between {sender_id} and {receiver_id}!")
    LOGGER.info(f"Trade complete: {sender_id} <-> {receiver_id}")
