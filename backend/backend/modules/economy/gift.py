from pyrogram import enums, errors, filters, types
from backend import LOGGER, app, user_collection
from backend.core.sessions import create_session, delete_session, get_session
from backend.core.user import get_user_data, update_user
from backend.core.utils import handle_errors, html_escape


@app.on_message(filters.command("gift"))
@handle_errors
async def gift_command(_, message: types.Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to the user you want to gift to.", parse_mode=enums.ParseMode.HTML)
        return
    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id:
        await message.reply_text("You cannot gift yourself!", parse_mode=enums.ParseMode.HTML)
        return
    if len(message.command) < 2:
        await message.reply_text("Usage: <code>/gift &lt;character_id&gt;</code>", parse_mode=enums.ParseMode.HTML)
        return
    character_id = message.command[1]
    sender_data = await get_user_data(sender_id)
    if not sender_data:
        await message.reply_text("You don't have any characters.")
        return
    characters = sender_data.get("characters", [])
    character_to_gift = next((c for c in characters if str(c.get("id")) == character_id), None)
    if not character_to_gift:
        await message.reply_text("You don't own this character.")
        return
    session_id = f"gift_{sender_id}_{receiver_id}_{character_id}"
    session_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "character": character_to_gift
    }
    await create_session(session_id, session_data)
    receiver_name = message.reply_to_message.from_user.first_name
    caption = (
        f"<b>Gift Confirmation</b>\n\n"
        f"Are you sure you want to gift <b>{html_escape(character_to_gift['name'])}</b> to <b>{html_escape(receiver_name)}</b>?\n"
        f"ID: <code>{character_id}</code>\n"
        f"This action cannot be undone."
    )
    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("Confirm", callback_data=f"gift_confirm:{session_id}"),
            types.InlineKeyboardButton("Cancel", callback_data=f"gift_cancel:{session_id}")
        ]
    ])
    await message.reply_text(caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
@app.on_callback_query(filters.regex(r"^gift_(confirm|cancel):(.+)"))
async def gift_callback(_, query: types.CallbackQuery):
    action, session_id = query.data.split(":", 1)
    session = await get_session(session_id)
    if not session:
        await query.answer("Session expired or invalid.", show_alert=True)
        await query.message.edit_text("This gift session has expired.")
        return
    sender_id = session["sender_id"]
    if query.from_user.id != sender_id:
        await query.answer("This is not your gift session!", show_alert=True)
        return
    if action == "gift_cancel":
        await delete_session(session_id)
        await query.message.edit_text("Gift cancelled.")
        await query.answer("Cancelled.")
        return
    receiver_id = session["receiver_id"]
    character = session["character"]
    char_id = character["id"]
    sender_db = await get_user_data(sender_id)
    if not sender_db or not sender_db.get("characters"):
        await query.answer("You no longer own this character.", show_alert=True)
        await delete_session(session_id)
        return
    sender_chars = sender_db["characters"]
    index_to_remove = -1
    for i, char in enumerate(sender_chars):
        if str(char.get("id")) == str(char_id):
            index_to_remove = i
            break
    if index_to_remove == -1:
        await query.answer("You no longer own this character.", show_alert=True)
        await delete_session(session_id)
        return
    # Atomic removal of exactly one instance
    from backend.core.user import remove_char_from_user, add_char_to_user

    if await remove_char_from_user(sender_id, str(char_id)):
        try:
            await add_char_to_user(receiver_id, character)
        except Exception as e:
            # Compensate: return the character to the sender so it is never lost.
            LOGGER.error(f"Gift delivery failed {sender_id} -> {receiver_id} | Char: {char_id}: {e}")
            try:
                await add_char_to_user(sender_id, character)
            except Exception:
                LOGGER.exception(f"CRITICAL: gift compensation failed, character {char_id} lost from {sender_id}")
            await query.answer("Gift failed. Your character was returned.", show_alert=True)
            await delete_session(session_id)
            return
    else:
        await query.answer("Failed to process gift. Please try again.", show_alert=True)
        await delete_session(session_id)
        return

    await delete_session(session_id)
    await query.message.edit_text(
        f"<b>Gift Sent!</b>\n\n"
        f"You successfully gifted <b>{html_escape(character['name'])}</b> to the fellow Collector!",
        parse_mode=enums.ParseMode.HTML
    )
    LOGGER.info(f"Gift: {sender_id} -> {receiver_id} | Char: {char_id}")
