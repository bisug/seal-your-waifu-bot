from pyrogram import enums, errors, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from Grabber import LOGGER, app, user_collection
from Grabber.core.sessions import create_session, delete_session, get_session
from Grabber.core.user import get_user_data, update_user
from Grabber.core.utils import html_escape


@app.on_message(filters.command(["transfer", "tranafer"]))
async def transfer_collection_command(_, message: types.Message):
    """
    Initiates a full character collection transfer (merge) to another user.
    """
    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ <b>Usage:</b> Reply to the user you want to transfer your collection to with <code>/transfer</code>",
            parse_mode=ParseMode.HTML
        )
        return

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("⚠️ You cannot transfer your collection to yourself!", parse_mode=ParseMode.HTML)
        return

    if message.reply_to_message.from_user.is_bot:
        await message.reply_text("⚠️ You cannot transfer your collection to a bot!", parse_mode=ParseMode.HTML)
        return

    # Fetch sender data to verify characters
    sender_data = await get_user_data(sender_id)
    if not sender_data or not sender_data.get("characters"):
        await message.reply_text("❌ You don't have any characters to transfer.", parse_mode=ParseMode.HTML)
        return

    char_count = len(sender_data["characters"])

    # Create session for confirmation
    session_id = f"transfer_{sender_id}_{receiver_id}"
    session_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "char_count": char_count,
        "step": 1
    }
    await create_session(session_id, session_data)

    receiver_name = message.reply_to_message.from_user.first_name
    caption = (
        f"⚠️ <b>COLLECTION TRANSFER: STEP 1/2</b> ⚠️\n\n"
        f"You are initiating a transfer of your <b>ENTIRE collection</b> ({char_count} characters) "
        f"to <b>{html_escape(receiver_name)}</b>.\n\n"
        f"🔴 <b>What happens?</b>\n"
        f"1. Your collection will be <b>merged</b> into theirs.\n"
        f"2. Your character list and count will be <b>CLEARED</b>.\n\n"
        f"<i>Do you wish to continue to the final confirmation?</i>"
    )

    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("Next ➡️", callback_data=f"transfer_next:{session_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"transfer_cancel:{session_id}")
        ]
    ])

    await message.reply_text(caption, reply_markup=markup, parse_mode=ParseMode.HTML)


@app.on_callback_query(filters.regex(r"^transfer_(next|confirm|cancel):(.+)"))
async def transfer_callback(_, query: types.CallbackQuery):
    action, session_id = query.data.split(":", 1)

    session = await get_session(session_id)
    if not session:
        await query.answer("❌ Session expired or invalid.", show_alert=True)
        await query.message.edit_text("❌ This transfer session has expired.")
        return

    sender_id = session["sender_id"]
    if query.from_user.id != sender_id:
        await query.answer("❌ This is not your transfer session!", show_alert=True)
        return

    if action == "transfer_cancel":
        await delete_session(session_id)
        await query.message.edit_text("✅ <b>Transfer cancelled.</b> Your collection is safe.", parse_mode=ParseMode.HTML)
        await query.answer("Cancelled.")
        return

    if action == "transfer_next":
        # Double confirm step
        receiver_id = session["receiver_id"]
        char_count = session["char_count"]
        
        # Update session step
        session["step"] = 2
        await create_session(session_id, session)

        receiver_user = await app.get_users(receiver_id)
        receiver_name = receiver_user.first_name if receiver_user else f"ID: {receiver_id}"

        caption = (
            f"🚫 <b>FINAL CONFIRMATION: STEP 2/2</b> 🚫\n\n"
            f"<b>ARE YOU ABSOLUTELY SURE?</b>\n\n"
            f"Target: <b>{html_escape(receiver_name)}</b>\n"
            f"Amount: <b>{char_count} characters</b>\n\n"
            f"⚠️ <b>THIS ACTION CANNOT BE UNDONE.</b>\n"
            f"Clicking 'Confirm' will empty your collection completely."
        )

        markup = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("✅ YES, MERGE COLLECTIONS", callback_data=f"transfer_confirm:{session_id}"),
                types.InlineKeyboardButton("❌ CANCEL", callback_data=f"transfer_cancel:{session_id}")
            ]
        ])

        await query.message.edit_text(caption, reply_markup=markup, parse_mode=ParseMode.HTML)
        await query.answer("Final step.")
        return

    if action == "transfer_confirm":
        # Check if we reached step 2
        if session.get("step") != 2:
            await query.answer("❌ Invalid sequence. Start over.", show_alert=True)
            return

        # Proceed with Transfer
        receiver_id = session["receiver_id"]
        
        # Re-fetch sender data to get fresh character list
        sender_data = await get_user_data(sender_id)
        if not sender_data or not sender_data.get("characters"):
            await query.answer("❌ You no longer have any characters.", show_alert=True)
            await delete_session(session_id)
            return

        characters_to_move = sender_data["characters"]
        num_chars = len(characters_to_move)

        try:
            # 1. Add all characters to receiver
            await update_user(receiver_id, {
                "$push": {"characters": {"$each": characters_to_move}},
                "$inc": {"char_count": num_chars}
            })

            # 2. Wipe sender's collection
            await update_user(sender_id, {
                "$set": {"characters": [], "char_count": 0}
            })

            await delete_session(session_id)

            # Notify success
            receiver_user = await app.get_users(receiver_id)
            receiver_name = receiver_user.first_name if receiver_user else f"ID: {receiver_id}"

            await query.message.edit_text(
                f"✅ <b>Collection Successfully Transferred!</b>\n\n"
                f"Moved <b>{num_chars}</b> characters to <b>{html_escape(receiver_name)}</b>.\n"
                f"Your harem is now empty.",
                parse_mode=ParseMode.HTML
            )
            
            # Log the event
            LOGGER.info(f"FULL TRANSFER: {sender_id} -> {receiver_id} ({num_chars} chars)")

            # Invalidate leaderboards as harem sizes changed
            from Grabber.core.cache import invalidate_leaderboard_cache
            await invalidate_leaderboard_cache()

        except Exception as e:
            LOGGER.error(f"Error during collection transfer {sender_id}->{receiver_id}: {e}")
            await query.answer("❌ An error occurred during the transfer. Please contact an admin.", show_alert=True)
