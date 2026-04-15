import math
import random
from collections import Counter
from typing import Any, Dict, List, Union

from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import LOGGER, WEB_APP_URL, app
from Grabber.core.cache import get_total_ranked_users, get_user_rank
from Grabber.core.keyboard import KeyboardBuilder, get_paginated_keyboard
from Grabber.core.progression import get_user_progress
from Grabber.core.utils import get_user_id_query, normalize_user_id
from Grabber.core.utils import html_escape as escape
from Grabber.core.utils import reply_media_dynamic

FORMATS = [
    "<b>{rarity}</b>\n└ {name} (<code>{id}</code>) ×{count}",
    "<code>{id}</code> - {name} [<b>{rarity}</b>] ×{count}",
]

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: types.Message):
    user_id = message.from_user.id
    await show_harem(message, user_id, 0)

@app.on_callback_query(filters.regex(r"^harem_view"))
async def harem_view_btn_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    # "self" is a special case used in /start — resolve to the caller's ID
    raw_id = data[1] if len(data) > 1 else "self"
    owner_id = query.from_user.id if raw_id == "self" else int(raw_id)

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your profile!", show_alert=True)

    await query.answer()
    await show_harem(query, owner_id, 0)

async def show_harem(message_obj: Union[types.Message, types.CallbackQuery], user_id: int, page: int):
    try:
        from Grabber.database import user_collection
        uid_int = normalize_user_id(user_id)
        user = await user_collection.find_one(get_user_id_query(uid_int))
        
        if not user or not user.get('characters'):
            text = "❌ <b>Harem is Empty</b>\n\nYour collection exists only in your dreams. Go hunt some characters!"
            if isinstance(message_obj, types.CallbackQuery):
                return await message_obj.answer(text, show_alert=True)
            return await message_obj.reply_text(text, parse_mode=ParseMode.HTML)

        all_chars = user['characters']
        char_counts = Counter(c.get('id') for c in all_chars)
        
        # Performance: Group characters BEFORE sorting for large collection speedup
        unique_chars_map = {}
        for char in all_chars:
            cid = char.get('id')
            if cid and cid not in unique_chars_map:
                unique_chars_map[cid] = char
        
        unique_chars = sorted(unique_chars_map.values(), key=lambda x: (x.get('anime', ''), x.get('name', '')))

        per_page = 7
        total_pages = math.ceil(len(unique_chars) / per_page)
        page = max(0, min(page, total_pages - 1))

        current_idx = user.get('current_format_index', 0)
        char_format = FORMATS[current_idx % len(FORMATS)]
        first_name = user.get('first_name', 'User')

        # Fetch Rank and Level for the Header
        progress = await get_user_progress(uid_int, user_data=user)
        rank = await get_user_rank(uid_int) or "N/A"
        total_ranked = await get_total_ranked_users() or "???"

        total_chars_count = user.get('char_count', len(all_chars))

        harem_text = (
            f"🎒 <b>{escape(first_name)}'s Collection</b>\n"
            f"💠 <b>Rank:</b> <code>#{rank}</code> / {total_ranked}\n"
            f"🆙 <b>Level:</b> <code>{progress['level']}</code>\n"
            f"📊 <b>Stats:</b> <code>{len(unique_chars)}</code> Unique | <code>{total_chars_count}</code> Total\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        start_idx = page * per_page
        current_slice = unique_chars[start_idx : start_idx + per_page]

        last_anime = ""
        for char in current_slice:
            anime = char.get('anime', 'Mixed')
            if anime != last_anime:
                harem_text += f"🎬 <b>{escape(anime)}</b>\n"
                last_anime = anime
                
            char_id = char.get('id', 'N/A')
            harem_text += char_format.format(
                anime=anime,
                rarity=char.get('rarity', 'Common'),
                id=char_id,
                name=escape(char.get('name', 'Unknown')),
                count=char_counts.get(char_id, 1)
            ) + "\n\n"

        harem_text += f"<i>Page {page + 1} of {total_pages}</i>"

        is_private = (message_obj.message if isinstance(message_obj, types.CallbackQuery) else message_obj).chat.type == enums.ChatType.PRIVATE
        
        markup = get_paginated_keyboard(page, total_pages, "h", uid_int, is_private)
        builder = KeyboardBuilder()
        builder.keyboard = markup.inline_keyboard.copy()
        builder.add_row(types.InlineKeyboardButton("🔍 Search Collection", switch_inline_query_current_chat=f"collection.{uid_int} "))
        markup = builder.build()

        try:
            pic = random.choice(all_chars).get('img_url')
        except Exception:
            pic = None

        if isinstance(message_obj, types.CallbackQuery):
            if pic:
                 await message_obj.edit_message_media(
                    media=types.InputMediaPhoto(media=pic, caption=harem_text, parse_mode=ParseMode.HTML),
                    reply_markup=markup
                )
            else:
                await message_obj.edit_message_text(text=harem_text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            if pic:
                await reply_media_dynamic(message_obj, pic,
                    caption=harem_text,
                    reply_markup=markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                 await message_obj.reply_text(harem_text, reply_markup=markup, parse_mode=ParseMode.HTML)

    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in show_harem: {e}", exc_info=True)
        if isinstance(message_obj, types.Message):
             await message_obj.reply_text("An error occurred while fetching your harem.")

@app.on_callback_query(filters.regex(r"^h:(p|n):"))
async def harem_nav_handler(_, query: types.CallbackQuery):
    try:
        data_parts = query.data.split(":")
        if len(data_parts) != 4:
            return await query.answer("❌ Invalid data!", show_alert=True)

        _, _, page_str, user_id_str = data_parts
        page = int(page_str)
        user_id = int(user_id_str)

        if query.from_user.id != user_id:
            return await query.answer("❌ This is not your harem!", show_alert=True)

        await query.answer()  # Dismiss spinner instantly
        await show_harem(query, user_id, page)
    except ValueError:
         await query.answer("❌ Invalid data format!", show_alert=True)
