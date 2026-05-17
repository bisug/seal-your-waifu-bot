import re
from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, app
from Grabber.core.user import get_user_data, update_user
from Grabber.core.utils import html_escape, reply_media_dynamic, handle_errors

@app.on_message(filters.command(["fav", "sfav"]))
@handle_errors
async def fav_handler(_, message: types.Message):
    user_id = message.from_user.id
    char_id = None
    
    # 1. Try to get ID from command argument
    if len(message.command) >= 2:
        char_id = message.command[1]
    
    # 2. Try to get ID from reply
    elif message.reply_to_message:
        reply = message.reply_to_message
        source_text = reply.caption or reply.text or ""
        # Regex to find ID: <code>ID</code> or (ID) or just ID if numeric
        # Assuming ID format from other modules: <code>(.*?)</code>
        match = re.search(r"<code>(.*?)</code>", source_text)
        if match:
            char_id = match.group(1)
        else:
            # Fallback: look for numeric ID if not in code blocks
            numeric_match = re.search(r"ID:\s*(\d+)", source_text, re.IGNORECASE)
            if numeric_match:
                char_id = numeric_match.group(1)
                
    if not char_id:
        return await message.reply_text("❌ Provide a character ID or reply to a character message.")

    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("❌ Your collection is empty.")

    character = next((c for c in user['characters'] if isinstance(c, dict) and str(c.get('id')) == str(char_id)), None)
    if not character:
        return await message.reply_text("❌ You don't own this character.")

    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("Set as Favorite", callback_data=f"fav_set:{char_id}:{user_id}"),
        types.InlineKeyboardButton("Cancel", callback_data=f"fav_cancel:{user_id}")
    ]])
    
    confirm_text = (
        f"Set <b>{html_escape(character.get('name'))}</b> as your favorite?\n\n"
        f"<b>ID:</b> <code>{char_id}</code>\n"
        f"<b>Anime:</b> {html_escape(character.get('anime', 'Unknown'))}\n"
        f"<b>Rarity:</b> {character.get('rarity', 'Common')}"
    )
    
    await reply_media_dynamic(message, character.get('img_url'),
        caption=confirm_text,
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^fav_set:"))
async def fav_set_handler(_, query: types.CallbackQuery):
    _, char_id, user_id = query.data.split(":")
    if query.from_user.id != int(user_id):
        return await query.answer("This is not for you!", show_alert=True)
    await update_user(int(user_id), {"$set": {"favorites": [char_id]}})
    try:
        await query.message.edit_caption(f"Character <code>{char_id}</code> is now your favorite!", parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass
    await query.answer("Favorites updated.")
@app.on_callback_query(filters.regex(r"fav_cancel"))
async def fav_cancel_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    owner_id = int(data[1]) if len(data) > 1 else 0
    if owner_id and query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)
    await query.message.delete()
