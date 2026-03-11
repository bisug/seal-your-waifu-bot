import math
import random
from Grabber.core.utils import html_escape as escape
from collections import Counter
from typing import List, Dict, Union, Any

from pyrogram import filters, types, enums, errors
from pyrogram.enums import ParseMode
from config import config
from Grabber import app, WEB_APP_URL
from Grabber import LOGGER
from Grabber.core.user import get_user_data

FORMATS = [
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷〔<b>{rarity}</b>〕 {name} (ID: <code>{id}</code>) ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ ᴷᴱʸ: <code>{id}</code> - {name} [Rarity: <b>{rarity}</b>] ×{count}",
]

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: types.Message):
    user_id = message.from_user.id
    await show_harem(message, user_id, 0)

@app.on_callback_query(filters.regex(r"^harem_view"))
async def harem_view_btn_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    owner_id = int(data[1]) if len(data) > 1 else query.from_user.id

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your profile!", show_alert=True)

    await show_harem(query, owner_id, 0)
    await query.answer()

async def show_harem(message_obj: Union[types.Message, types.CallbackQuery], user_id: int, page: int):
    try:
        user = await get_user_data(user_id)
        if not user or not user.get('characters'):
            text = "❌ <b>You don't have any characters yet!</b>\n\n<i>Go catch some waifus first!</i>"
            if isinstance(message_obj, types.CallbackQuery):
                return await message_obj.answer(text, show_alert=True)
            return await message_obj.reply_text(text, parse_mode=ParseMode.HTML)

        all_chars = user['characters']


        char_counts = Counter(c.get('id') for c in all_chars)


        sorted_chars = sorted(all_chars, key=lambda x: (x.get('anime', ''), x.get('id', '')))


        unique_chars: List[Dict[str, Any]] = []
        seen_ids = set()
        for char in sorted_chars:
            char_id = char.get('id')
            if char_id not in seen_ids:
                unique_chars.append(char)
                seen_ids.add(char_id)

        per_page = 7
        total_pages = math.ceil(len(unique_chars) / per_page)
        page = max(0, min(page, total_pages - 1))

        current_idx = user.get('current_format_index', 0)
        char_format = FORMATS[current_idx % len(FORMATS)]

        first_name = user.get('first_name', 'User')


        header_lines = [
            f"🎒 <b>{escape(first_name)}'s Collection</b>",
            "━━━━━━━━━━━━━━━━━━━━━",
            f"📑 <b>Page:</b> <code>{page + 1}/{total_pages}</code>",
            f"✨ <b>Characters:</b> <code>{len(all_chars)}</code> total",
            ""
        ]
        harem_text = "\n".join(header_lines)


        start_idx = page * per_page
        end_idx = start_idx + per_page
        current_slice = unique_chars[start_idx:end_idx]

        for char in current_slice:
            char_id = char.get('id', 'N/A')
            harem_text += char_format.format(
                anime=char.get('anime', 'Mixed'),
                page=page + 1,
                total_pages=total_pages,
                rarity=char.get('rarity', 'Common'),
                id=char_id,
                name=char.get('name', 'Unknown'),
                count=char_counts.get(char_id, 1)
            ) + "\n"

        harem_text += "━━━━━━━━━━━━━━━━━━━━━\n"

        is_private = False
        if isinstance(message_obj, types.CallbackQuery):
            is_private = message_obj.message.chat.type == enums.ChatType.PRIVATE
        else:
            is_private = message_obj.chat.type == enums.ChatType.PRIVATE

        markup = _build_harem_markup(page, total_pages, user_id, is_private)


        try:
            pic = random.choice(all_chars).get('img_url')
        except (IndexError, KeyError):

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
                await message_obj.reply_photo(
                    photo=pic,
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

def _build_harem_markup(page: int, total_pages: int, user_id: int, is_private: bool) -> types.InlineKeyboardMarkup:

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

    keyboard = [
        nav_buttons,
    ]
    if is_private:
        keyboard.append([types.InlineKeyboardButton("🌐 Open Web App", web_app=types.WebAppInfo(url=WEB_APP_URL))])
    else:
        bot_username = getattr(config, "BOT_USERNAME", "Seal_Your_Waifu_Bot")
        keyboard.append([types.InlineKeyboardButton("🌐 Launch Web App (DM)", url=f"https://t.me/{bot_username}?start=webapp")])

    keyboard.extend([
        [types.InlineKeyboardButton("🔍 Search Harem", switch_inline_query_current_chat=f"collection.{user_id} ")],
        [types.InlineKeyboardButton("🌐 Global Search", switch_inline_query_current_chat="")]
    ])

    return types.InlineKeyboardMarkup([row for row in keyboard if row])

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

        await show_harem(query, user_id, page)
        await query.answer()
    except ValueError:
         await query.answer("❌ Invalid data format!", show_alert=True)
