import re
import time
import asyncio
from html import escape
from telegram import (
    Update,
    InlineQueryResultPhoto,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    InlineQueryHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from Grabber import user_collection, collection, application

# Global cache for performance
global_guess_cache = {}

async def get_global_guess_count(char_id):
    """Fetches and caches global guess count."""
    if char_id in global_guess_cache:
        return global_guess_cache[char_id]
    global_count = await user_collection.count_documents({'characters.id': char_id})
    global_guess_cache[char_id] = global_count
    return global_count

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset or 0)
    characters = []
    user = None

    if query.startswith('collection.'):
        parts = query.split(' ')
        user_id_part = parts[0].split('.')[1] if len(parts[0].split('.')) > 1 else None
        search_terms = ' '.join(parts[1:]) if len(parts) > 1 else ""

        if user_id_part and user_id_part.isdigit():
            user_id = int(user_id_part)
            user = await user_collection.find_one({'id': user_id}, {'characters': 1, 'id': 1, 'first_name': 1})

            if user and isinstance(user.get('characters'), list):
                characters = list({char['id']: char for char in user['characters'] if isinstance(char, dict)}.values())
                if search_terms:
                    search_regex = re.compile(re.escape(search_terms), re.IGNORECASE)
                    characters = [
                        char for char in characters
                        if search_regex.search(char.get('name', '')) or search_regex.search(char.get('anime', ''))
                    ]
    else:
        filter_query = {}
        if query:
            search_regex = re.compile(re.escape(query), re.IGNORECASE)
            filter_query = {"$or": [{"name": search_regex}, {"anime": search_regex}]}

        characters = await collection.find(filter_query, {
            "id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1
        }).skip(offset).limit(10).to_list(None)

    next_offset = str(offset + len(characters)) if len(characters) == 10 else ""

    # Pre-fetch guess counts
    tasks = [get_global_guess_count(char["id"]) for char in characters]
    global_counts = await asyncio.gather(*tasks)

    results = []
    for i, character in enumerate(characters):
        char_id = str(character["id"])
        global_count = global_counts[i]
        name = escape(character['name'])
        anime = escape(character['anime'])
        rarity = escape(character['rarity'])

        if query.startswith("collection.") and user:
            first_name = escape(user.get("first_name", "Unknown"))
            caption = (
                f"⛩ 【{first_name}】's harem\n\n"
                f"☘️ Name: {name} (x1)\n"
                f"🟠 Rarity: {rarity}\n"
                f"⚜️ Anime: {anime} (1/4)\n\n"
                f"🆔: {char_id} - Needed for trading/gifting"
            )
        else:
            caption = (
                f"» 𝐖𝐚𝐭𝐜𝐡 𝐭𝐡𝐢𝐬 𝐚𝐰𝐞𝐬𝐨𝐦𝐞 𝐂𝐡𝐚𝐫𝐚𝐜𝐭𝐞𝐫 «\n\n"
                f"🌸 {name}\n"
                f"🏖️ {anime}\n"
                f"🎭 {rarity}\n"
                f"🆔 {char_id}\n\n"
            )

        keyboard = InlineKeyboardMarkup([
              [InlineKeyboardButton("📊 How many users have?", callback_data=f"character_count_{char_id}")]

        ])

        results.append(
            InlineQueryResultPhoto(
                id=f"{char_id}_{int(time.time())}",
                thumbnail_url=character['img_url'],
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

async def guessed_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Prevent loading spinner

    try:
        char_id = query.data.split("_")[2]
    except IndexError:
        await query.edit_message_text("Invalid callback data.", parse_mode="HTML")
        return

    try:
        result = await user_collection.aggregate([
            {"$match": {"characters.id": char_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": char_id}},
            {"$group": {"_id": "$id"}},  # Get unique user IDs
            {"$count": "user_count"}
        ]).to_list(length=1)

        global_count = result[0]["user_count"] if result else 0

        if global_count == 0:
            await query.answer("🚫 No users currently own this character.", show_alert=True)
        else:
            await query.answer(f"📊 This character is owned by {global_count} users!", show_alert=True)

    except Exception as e:
        await query.answer(f"❌ An error occurred: {str(e)}", show_alert=True)


# Register handlers
application.add_handler(CallbackQueryHandler(guessed_callback, pattern=r'^character_count_\d+$'))


application.add_handler(InlineQueryHandler(inlinequery))
            
