from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, app
from Grabber.core.user import get_user_data, update_user
from Grabber.core.utils import html_escape, reply_media_dynamic
@app.on_message(filters.command(["fav", "sfav"]))
async def fav_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Provide a character ID.")
    char_id = message.command[1]
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("Your collection is empty.")
    character = next((c for c in user['characters'] if isinstance(c, dict) and str(c.get('id')) == str(char_id)), None)
    if not character:
        return await message.reply_text("You don't own this character.")
    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("Set as Favorite", callback_data=f"fav_set:{char_id}:{user_id}"),
        types.InlineKeyboardButton("Cancel", callback_data=f"fav_cancel:{user_id}")
    ]])
    await reply_media_dynamic(message, character.get('img_url'),
        caption=f"Set <b>{html_escape(character.get('name'))}</b> as your favorite?",
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
