import math
import random
from html import escape
from itertools import groupby
from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import collection, LOGGER
from Grabber.core.user import get_user_data

FORMATS = [
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷〔<b>{rarity}</b>〕 {name} (ID: <code>{id}</code>) ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ ᴷᴱʸ: <code>{id}</code> - {name} [Rarity: <b>{rarity}</b>] ×{count}",
]

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: types.Message):
    user_id = message.from_user.id
    await show_harem(message, user_id, 0)

@app.on_callback_query(filters.regex(r"^harem_view$"))
async def harem_view_btn_handler(_, query: types.CallbackQuery):
    await show_harem(query, query.from_user.id, 0)
    await query.answer()

async def show_harem(message_obj, user_id, page):
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        text = "❌ <b>You don't have any characters yet!</b>\n\n<i>Go catch some waifus first!</i>"
        if isinstance(message_obj, types.CallbackQuery):
            return await message_obj.answer(text, show_alert=True)
        return await message_obj.reply_text(text, parse_mode=enums.ParseMode.HTML)

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

    first_name = user.get('first_name', 'User')
    harem_text = f"🎒 <b>{escape(first_name)}'s Collection</b>\n"
    harem_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    harem_text += f"📑 <b>Page:</b> <code>{page + 1}/{total_pages}</code>\n"
    harem_text += f"✨ <b>Characters:</b> <code>{len(chars)}</code> total\n\n"

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

    harem_text += f"━━━━━━━━━━━━━━━━━━━━━\n"

    # Navigation buttons
    nav_buttons = []
    if total_pages > 1:
        prev_btn = types.InlineKeyboardButton("⬅️ Prev", callback_data=f"h:p:{page-1}:{user_id}")
        next_btn = types.InlineKeyboardButton("Next ➡️", callback_data=f"h:n:{page+1}:{user_id}")
        if page == 0:
            nav_buttons = [next_btn]
        elif page == total_pages - 1:
            nav_buttons = [prev_btn]
        else:
            nav_buttons = [prev_btn, next_btn]

    markup = types.InlineKeyboardMarkup([
        nav_buttons,
        [types.InlineKeyboardButton("🔍 Search Harem", switch_inline_query_current_chat=f"collection.{user_id} ")],
        [types.InlineKeyboardButton("🌐 Global Search", switch_inline_query_current_chat="")]
    ])

    try:
        # Use a random character's image for the harem cover
        pic = random.choice(chars)['img_url']
        
        if isinstance(message_obj, types.CallbackQuery):
            await message_obj.edit_message_media(
                media=types.InputMediaPhoto(media=pic, caption=harem_text, parse_mode=enums.ParseMode.HTML),
                reply_markup=markup
            )
        else:
            await message_obj.reply_photo(
                photo=pic,
                caption=harem_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
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
