import uuid
from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, app, client
from Grabber.core.cache import invalidate_user_cache
from Grabber.core.sessions import create_session, delete_session, get_session
from Grabber.core.user import get_user_data
from Grabber.core.utils import get_user_id_query, handle_errors, html_escape
from Grabber.modules.progression.quests import update_quest_progress
@app.on_message(filters.command("trade") & filters.group)
@handle_errors
async def trade_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to trade!", parse_mode=enums.ParseMode.HTML)
    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id:
        return await message.reply_text("No self-trading!", parse_mode=enums.ParseMode.HTML)
    if len(message.command) != 3:
        return await message.reply_text("Usage: <code>/trade &lt;your_char_id&gt; &lt;their_char_id&gt;</code>", parse_mode=enums.ParseMode.HTML)
    s_char_id, r_char_id = message.command[1], message.command[2]
    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)
    if not sender or not receiver:
        return await message.reply_text("Database error.", parse_mode=enums.ParseMode.HTML)
    s_char = next((c for c in sender.get('characters', []) if str(c.get('id')) == s_char_id), None)
    r_char = next((c for c in receiver.get('characters', []) if str(c.get('id')) == r_char_id), None)
    if not s_char:
        return await message.reply_text("You don't own that character.", parse_mode=enums.ParseMode.HTML)
    if not r_char:
        return await message.reply_text("They don't own that character.", parse_mode=enums.ParseMode.HTML)
    if str(s_char['id']) in (sender.get('locked') or []):
        return await message.reply_text("🔒 That character is locked and cannot be traded.", parse_mode=enums.ParseMode.HTML)
    if str(r_char['id']) in (receiver.get('locked') or []):
        return await message.reply_text("🔒 Their character is locked and cannot be traded.", parse_mode=enums.ParseMode.HTML)
    # Nonce prevents two concurrent trades between the same pair colliding
    # on one shared session key.
    trade_id = f"tr_{uuid.uuid4().hex}"
    await create_session(trade_id, {"s_char": s_char, "r_char": r_char, "s_id": sender_id, "r_id": receiver_id})
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("Confirm", callback_data=f"tr_c:{trade_id}"),
         types.InlineKeyboardButton("Cancel", callback_data=f"tr_x:{trade_id}")]
    ])
    await message.reply_to_message.reply_text(
        f"<a href=\"tg://user?id={receiver_id}\">{html_escape(message.reply_to_message.from_user.first_name)}</a>, accept trade?\n\n"
        f"<b>Give:</b> {html_escape(s_char['name'])}\n"
        f"<b>Take:</b> {html_escape(r_char['name'])}",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^tr_(c|x):"))
async def trade_callback_handler(_, query: types.CallbackQuery):
    action, trade_id = query.data.split(":")
    trade_info = await get_session(trade_id)
    if not trade_info:
        return await query.answer("Trade expired or handled.", show_alert=True)
    sender_id, receiver_id = trade_info["s_id"], trade_info["r_id"]
    if action == "x":
        if query.from_user.id not in [sender_id, receiver_id]:
            return await query.answer("Not yours!", show_alert=True)
        await delete_session(trade_id)
        try:
            await query.message.edit_text("Trade canceled.", parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return
    if query.from_user.id != receiver_id:
        return await query.answer("This is for the receiver to accept!", show_alert=True)
    s_char, r_char = trade_info["s_char"], trade_info["r_char"]
    sender = await get_user_data(sender_id)
    receiver = await get_user_data(receiver_id)
    if not sender or not receiver:
        return await query.answer("User data not found.", show_alert=True)
    s_char_verify = next((c for c in sender.get('characters', []) if c.get('id') == s_char['id']), None)
    r_char_verify = next((c for c in receiver.get('characters', []) if c.get('id') == r_char['id']), None)
    if not s_char_verify or not r_char_verify:
        await delete_session(trade_id)
        return await query.message.edit_text(
            "One of the characters is no longer available.",
            parse_mode=enums.ParseMode.HTML
        )
    # 1. Processing trade - delete session first to prevent double-click race
    await query.answer("Processing trade...", cache_time=1)
    await delete_session(trade_id)
    # 2. Swap exactly one instance using positional $set to avoid mass-deletion bug
    from Grabber.database import user_collection
    try:
        async with client.start_session() as mongo_session:
            async with await mongo_session.start_transaction():
                sender_result = await user_collection.update_one(
                    {**get_user_id_query(sender_id), "characters.id": s_char['id']},
                    {"$set": {"characters.$": r_char}, "$inc": {"version": 1}},
                    session=mongo_session
                )
                if sender_result.modified_count == 0:
                    raise ValueError(f"Sender {sender_id} no longer owns char {s_char['id']}")
                receiver_result = await user_collection.update_one(
                    {**get_user_id_query(receiver_id), "characters.id": r_char['id']},
                    {"$set": {"characters.$": s_char}, "$inc": {"version": 1}},
                    session=mongo_session
                )
                if receiver_result.modified_count == 0:
                    raise ValueError(f"Receiver {receiver_id} no longer owns char {r_char['id']}")
        await invalidate_user_cache(sender_id)
        await invalidate_user_cache(receiver_id)
    except Exception as e:
        LOGGER.error(f"Trade DB Error: {e}")
        return await query.message.edit_text("Trade failed: One of the characters was no longer available.", parse_mode=enums.ParseMode.HTML)
    from Grabber.modules.progression.achievements import check_achievements
    await update_quest_progress(sender_id, "trader", 1)
    await update_quest_progress(receiver_id, "trader", 1)
    await check_achievements(sender_id)
    await check_achievements(receiver_id)
    await query.message.edit_text(
        f"<b>Trade successful!</b>\n"
        f"<a href=\"tg://user?id={sender_id}\">Collector {sender_id}</a> ↔️ <a href=\"tg://user?id={receiver_id}\">Collector {receiver_id}</a>",
        parse_mode=enums.ParseMode.HTML
    )
    LOGGER.info(f"Trade complete: {sender_id} <-> {receiver_id}")
