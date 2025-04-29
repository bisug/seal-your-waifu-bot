from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from itertools import groupby
import math
import random
from html import escape
from Grabber import collection, user_collection, application

# Define distinct character display formats
character_formats = [
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷〔{rarity}〕 {name} (ID: {id}) ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ ᴷᴱʸ: {id} - {name} [Rarity: {rarity}] ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ ᴥ {name} ᴥ | ID: {id} | Rarity: {rarity} ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ {name} ⦠ ID: {id} ⦠ Rarity: {rarity} ×{count}",
    "⧉ {anime} [🎮] ⦋{page}/{total_pages}⦌\n⤷ [⭐] {name} (#ID: {id}) | Rarity: {rarity} ×{count}"
]

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})

    if not user or 'characters' not in user or not isinstance(user['characters'], list) or not user['characters']:
        text = "❌ You have not collected any characters yet!"
        if update.message:
            await update.message.reply_text(text)
        else:
            await update.callback_query.edit_message_text(text)
        return

    characters = [c for c in user['characters'] if isinstance(c, dict) and 'id' in c and 'anime' in c and 'name' in c]

    if not characters:
        text = "❌ Your character list is empty!"
        if update.message:
            await update.message.reply_text(text)
        else:
            await update.callback_query.edit_message_text(text)
        return

    characters = sorted(characters, key=lambda x: (x['anime'], x['id']))
    character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
    unique_characters = list({character['id']: character for character in characters}.values())

    characters_per_page = 7
    total_pages = math.ceil(len(unique_characters) / characters_per_page)
    page = max(0, min(page, total_pages - 1))

    current_format_index = user.get('current_format_index', 0)
    character_format = character_formats[current_format_index]

    harem_message = f"🐰 {escape(update.effective_user.first_name)} ┊ **Harem - Page {page + 1}/{total_pages}**\n\n"

    current_characters = unique_characters[page * characters_per_page:(page + 1) * characters_per_page]
    grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

    for anime, chars in grouped_characters.items():
        total_anime_characters = await collection.count_documents({'anime': anime})
        harem_message += f"🎬 **{anime}** ({len(chars)}/{total_anime_characters})\n━━━━━━━━━━━━━━━━━\n"

        for char in chars:
            count = character_counts[char['id']]
            rarity = char.get("rarity", "Unknown")
            harem_message += character_format.format(
                anime=char['anime'],
                page=page + 1,
                total_pages=total_pages,
                rarity=rarity,
                id=char['id'],
                name=char['name'],
                count=count
            ) + "\n"
        harem_message += "━━━━━━━━━━━━━━━━━\n"

    total_count = len(user['characters'])
    keyboard = [[InlineKeyboardButton(f"📜 Full Collection ({total_count})", switch_inline_query_current_chat=f"collection.{user_id}")]]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem:{page-1}:{user_id}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"harem:{page+1}:{user_id}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    favorite_character = next((c for c in characters if 'favorites' in user and c['id'] in user['favorites']), None)
    if not favorite_character:
        favorite_character = random.choice(characters) if characters else None

    if update.message:
        if favorite_character and 'img_url' in favorite_character:
            await update.message.reply_photo(photo=favorite_character['img_url'], caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if update.callback_query.message.caption != harem_message:
            await update.callback_query.edit_message_caption(caption=harem_message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, user_id = query.data.split(':')
    page = int(page)
    user_id = int(user_id)

    if query.from_user.id != user_id:
        await query.answer("⚠️ You can't view someone else's Harem!", show_alert=True)
        return

    await harem(update, context, page)

async def hstyle(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    current_format_index = user.get('current_format_index', 0)

    # Prepare example data for format display
    anime_example = "Honkai Star Rail"
    page_example = 1
    total_pages_example = 86
    rarity_example = "🟡"
    name_example = "Stelle"
    id_example = 3547
    count_example = 1

    # Generate current format message
    current_format = character_formats[current_format_index].format(
        anime=anime_example,
        page=page_example,
        total_pages=total_pages_example,
        rarity=rarity_example,
        id=id_example,
        name=name_example,
        count=count_example
    )

    keyboard = [
        [InlineKeyboardButton("Set", callback_data=f"set_format:{current_format_index}:{user_id}")],
        [InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_format:{user_id}"),
         InlineKeyboardButton("➡️ Next", callback_data=f"next_format:{user_id}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⧉ Select a new format:\n\n{current_format}",
        reply_markup=reply_markup
    )

async def select_format(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, format_index, user_id = query.data.split(':')
    format_index = int(format_index)
    user_id = int(user_id)

    await user_collection.update_one({'id': user_id}, {'$set': {'current_format_index': format_index}})
    await query.answer(f"Format set to Format {format_index + 1}.")
    await hstyle(update, context)

async def next_format(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split(':')[1])
    user = await user_collection.find_one({'id': user_id})
    current_format_index = user.get('current_format_index', 0)

    next_format_index = (current_format_index + 1) % len(character_formats)

    # Prepare example data for next format display
    anime_example = "Honkai Star Rail"
    page_example = 1
    total_pages_example = 86
    rarity_example = "🟡"
    name_example = "Stelle"
    id_example = 3547
    count_example = 1

    # Generate next format message
    next_format_message = character_formats[next_format_index].format(
        anime=anime_example,
        page=page_example,
        total_pages=total_pages_example,
        rarity=rarity_example,
        id=id_example,
        name=name_example,
        count=count_example
    )

    await query.answer(f"Next format is Format {next_format_index + 1}.")
    await query.message.edit_text(
        f"⧉ Select a new format:\n\n{next_format_message}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Set", callback_data=f"set_format:{next_format_index}:{user_id}")],
            [InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_format:{user_id}"),
             InlineKeyboardButton("➡️ Next", callback_data=f"next_format:{user_id}")]
        ])
    )

async def prev_format(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split(':')[1])
    user = await user_collection.find_one({'id': user_id})
    current_format_index = user.get('current_format_index', 0)

    prev_format_index = (current_format_index - 1) % len(character_formats)

    # Prepare example data for previous format display
    anime_example = "Honkai Star Rail"
    page_example = 1
    total_pages_example = 86
    rarity_example = "🟡"
    name_example = "Stelle"
    id_example = 3547
    count_example = 1

    # Generate previous format message
    prev_format_message = character_formats[prev_format_index].format(
        anime=anime_example,
        page=page_example,
        total_pages=total_pages_example,
        rarity=rarity_example,
        id=id_example,
        name=name_example,
        count=count_example
    )

    await query.answer(f"Previous format is Format {prev_format_index + 1}.")
    await query.message.edit_text(
        f"⧉ Select a new format:\n\n{prev_format_message}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Set", callback_data=f"set_format:{prev_format_index}:{user_id}")],
            [InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_format:{user_id}"),
             InlineKeyboardButton("➡️ Next", callback_data=f"next_format:{user_id}")]
        ])
    )

application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem', block=False))
application.add_handler(CommandHandler("hstyle", hstyle, block=False))
application.add_handler(CallbackQueryHandler(select_format, pattern='^select_format:', block=False))
application.add_handler(CallbackQueryHandler(next_format, pattern='^next_format:', block=False))
application.add_handler(CallbackQueryHandler(prev_format, pattern='^prev_format:', block=False))
    
