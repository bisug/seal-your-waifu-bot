import math
import random
from html import escape
from itertools import groupby
from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import collection, LOGGER
from Grabber.core.user import get_user_data

FORMATS = [
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷〔{rarity}〕 {name} (ID: {id}) ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ ᴷᴱʸ: {id} - {name} [Rarity: {rarity}] ×{count}",
]

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: types.Message):
    user_id = message.from_user.id
    await show_harem(message, user_id, 0)

async def show_harem(message_obj, user_id, page):
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        text = "❌ You don't have any characters!"
        return await (message_obj.edit_text(text) if isinstance(message_obj, types.Message) and message_obj.from_user.id == app.me.id else message_obj.reply_text(text))

    chars = sorted(user['characters'], key=lambda x: (x.get('anime', ''), x.get('id', '')))
    
    # Logic: Group and count
    id_counts = {k: len(list(v)) for k, v in groupby(chars, key=lambda x: x.get('id', ''))}
    unique_chars = []
    seen = set()
    for c in chars:
        if c.get('id') not in seen:
            unique_chars.append(c)
            seen.add(c.get('id'))

    per_page = 7
    total_pages = math.ceil(len(unique_chars) / per_page)
    page = max(0, min(page, total_pages - 1))
    
    current_idx = user.get('current_format_index', 0)
    char_format = FORMATS[current_idx % len(FORMATS)]

    harem_text = f"🐰 **{escape(user.get('first_name', 'User'))}'s Harem**\n"
    harem_text += f"Page {page + 1}/{total_pages}\n\n"

    current_slice = unique_chars[page * per_page : (page + 1) * per_page]
    
    for char in current_slice:
        harem_text += char_format.format(
            anime=char.get('anime', 'Mixed'),
            page=page + 1,
            total_pages=total_pages,
            rarity=char.get('rarity', 'Common'),
            id=char.get('id', 'N/A'),
            name=char.get('name', 'Unknown'),
            count=id_counts.get(char.get('id'), 1)
        ) + "\n"

    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"h:p:{page-1}:{user_id}"),
            types.InlineKeyboardButton("Next ➡️", callback_data=f"h:n:{page+1}:{user_id}")
        ] if total_pages > 1 else [],
        [types.InlineKeyboardButton("Full Collection", switch_inline_query_current_chat=f"collection.{user_id}")]
    ])

    try:
        if isinstance(message_obj, types.CallbackQuery):
            await message_obj.edit_message_media(
                media=types.InputMediaPhoto(media=random.choice(chars)['img_url'], caption=harem_text),
                reply_markup=markup
            )
        else:
            await message_obj.reply_photo(
                photo=random.choice(chars)['img_url'],
                caption=harem_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.MARKDOWN
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in show_harem: {e}")

@app.on_callback_query(filters.regex(r"^h:(p|n):"))
async def harem_nav_handler(_, query: types.CallbackQuery):
    _, _, page, user_id = query.data.split(":")
    if query.from_user.id != int(user_id):
        return await query.answer("❌ This is not your harem!", show_alert=True)
    
    await show_harem(query, int(user_id), int(page))
    await query.answer()
