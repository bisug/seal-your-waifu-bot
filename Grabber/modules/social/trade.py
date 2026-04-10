from pyrogram import enums, filters, types, errors
from pyrogram.enums import ButtonStyle, ParseMode
from Grabber import app
from Grabber import LOGGER
from Grabber.core.user import get_user_data, update_user
from Grabber.core.utils import html_escape
from Grabber.core.sessions import create_session, get_session, delete_session
from Grabber.modules.progression.quests import update_quest_progress

@app.on_message(filters.command("trade") & filters.group)
async def trade_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to trade!", parse_mode=ParseMode.HTML)

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        return await message.reply_text("⚠️ No self-trading!", parse_mode=ParseMode.HTML)

    if len(message.command) != 3:
        return await message.reply_text("❌ Usage: <code>/trade &lt;your_char_id&gt; &lt;their_char_id&gt;</code>", parse_mode=ParseMode.HTML)

    s_char_id, r_char_id = message.command[1], message.command[2]

    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)

    if not sender or not receiver:
        return await message.reply_text("❌ Database error.", parse_mode=ParseMode.HTML)


    s_char = next((c for c in sender.get('characters', []) if str(c.get('id')) == s_char_id), None)
    r_char = next((c for c in receiver.get('characters', []) if str(c.get('id')) == r_char_id), None)

    if not s_char:
        return await message.reply_text("❌ You don't own that character.", parse_mode=ParseMode.HTML)
    if not r_char:
        return await message.reply_text("❌ They don't own that character.", parse_mode=ParseMode.HTML)


    trade_id = f"tr_{sender_id}_{receiver_id}"
    await create_session(trade_id, {"s_char": s_char, "r_char": r_char, "s_id": sender_id, "r_id": receiver_id})

    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("✅ Confirm", callback_data=f"tr_c:{trade_id}"),
         types.InlineKeyboardButton("❌ Cancel", callback_data=f"tr_x:{trade_id}")]
    ])

    await message.reply_to_message.reply_text(
        f"🤝 <a href=\"tg://user?id={receiver_id}\">{html_escape(message.reply_to_message.from_user.first_name)}</a>, accept trade?\n\n"
        f"📤 <b>Give:</b> {html_escape(s_char['name'])}\n"
        f"📥 <b>Take:</b> {html_escape(r_char['name'])}",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^tr_(c|x):"))
async def trade_callback_handler(_, query: types.CallbackQuery):
    action, trade_id = query.data.split(":")


    trade_info = await get_session(trade_id)

    if not trade_info:
        return await query.answer("❌ Trade expired or handled.", show_alert=True)

    sender_id, receiver_id = trade_info["s_id"], trade_info["r_id"]

    if action == "x":
        if query.from_user.id not in [sender_id, receiver_id]:
            return await query.answer("❌ Not yours!", show_alert=True)
        await delete_session(trade_id)
        try:
            await query.message.edit_text("❌ Trade canceled.", parse_mode=ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return

    if query.from_user.id != receiver_id:
        return await query.answer("❌ This is for the receiver to accept!", show_alert=True)

    s_char, r_char = trade_info["s_char"], trade_info["r_char"]

                                    # Verification: Ensure both still own the characters using ID-based check
    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)

    s_char_verify = next((c for c in sender.get('characters', []) if c.get('id') == s_char['id']), None)
    r_char_verify = next((c for c in receiver.get('characters', []) if c.get('id') == r_char['id']), None)

    if not s_char_verify or not r_char_verify:
        await delete_session(trade_id)
        return await query.message.edit_text(
            "❌ One of the characters is no longer available.",
            parse_mode=ParseMode.HTML
        )

    # 1. Processing trade - delete session first to prevent double-click race
    await query.answer("Processing trade...", cache_time=1)
    await delete_session(trade_id)

    # 2. Atomic Database Updates
    from Grabber.database import user_collection
    try:
        sender_result = await user_collection.update_one(
            {"id": {"$in": [sender_id, str(sender_id)]}, "characters.id": s_char['id']},
            {
                "$pull": {"characters": {"id": s_char['id']}},
                "$push": {"characters": r_char}
            }
        )
        if sender_result.modified_count == 0:
            raise ValueError(f"Sender {sender_id} no longer owns char {s_char['id']}")

        receiver_result = await user_collection.update_one(
            {"id": {"$in": [receiver_id, str(receiver_id)]}, "characters.id": r_char['id']},
            {
                "$pull": {"characters": {"id": r_char['id']}},
                "$push": {"characters": s_char}
            }
        )
        if receiver_result.modified_count == 0:
            # Compensate: give the sender their char back
            await user_collection.update_one(
                {"id": {"$in": [sender_id, str(sender_id)]}},
                {"$pull": {"characters": {"id": r_char['id']}}, "$push": {"characters": s_char}}
            )
            raise ValueError(f"Receiver {receiver_id} no longer owns char {r_char['id']}, rolled back.")

        from Grabber.core.cache import invalidate_user_cache
        await invalidate_user_cache(sender_id)
        await invalidate_user_cache(receiver_id)

    except Exception as e:
        LOGGER.error(f"Trade DB Error: {e}")
        return await query.message.edit_text("❌ Trade failed: One of the characters was no longer available.", parse_mode=ParseMode.HTML)

    # 3. Quests & Achievements
    await update_quest_progress(sender_id, "trader", 1)
    await update_quest_progress(receiver_id, "trader", 1)

    await query.message.edit_text(
        f"✅ Trade successful between <code>{sender_id}</code> and <code>{receiver_id}</code>!",
        parse_mode=ParseMode.HTML
    )
    LOGGER.info(f"Trade complete: {sender_id} <-> {receiver_id}")
