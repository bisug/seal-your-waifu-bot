import re
import time
from html import escape
from telegram import (
    InlineQueryResultPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    InlineQueryHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from Grabber import collection, user_collection, application  # अपने env के हिसाब से import करें

# Cache (अगर चाहें तो बाद में अपग्रेड कर सकते हैं)
global_guess_cache = {}

async def get_global_guess_count(char_id: str) -> int:
    if char_id in global_guess_cache:
        return global_guess_cache[char_id]
    count = await user_collection.count_documents({'characters.id': char_id})
    global_guess_cache[char_id] = count
    return count

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query_text = update.inline_query.query.strip()
    # DB से characters ले लें (यहां limit 10, आप जरूरत अनुसार बदल सकते हैं)
    filter_query = {}
    if query_text:
        regex = re.compile(re.escape(query_text), re.IGNORECASE)
        filter_query = {"$or": [{"name": regex}, {"anime": regex}]}
    characters = await collection.find(filter_query, {
        "id": 1, "name":1, "anime":1, "rarity":1, "img_url":1
    }).limit(10).to_list(length=10)

    results = []
    for character in characters:
        char_id = str(character["id"])
        name = escape(character["name"])
        anime = escape(character["anime"])
        rarity = escape(character["rarity"])

        caption = (
            f"🌸 <b>{name}</b>\n"
            f"🎬 Anime: {anime}\n"
            f"🔮 Rarity: {rarity}\n"
            f"🆔 ID: {char_id}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 How many users have?", callback_data=f"character_count:{char_id}")]
        ])

        results.append(
            InlineQueryResultPhoto(
                id=f"{char_id}_{int(time.time())}",
                photo_url=character["img_url"],
                thumbnail_url=character["img_url"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        )

    await update.inline_query.answer(results, cache_time=5)

async def guessed_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    await query.answer()  # spinner हटाने के लिए जरूरी

    if not data.startswith("character_count:"):
        await query.edit_message_text("⚠️ Invalid callback data.", parse_mode="HTML")
        return

    char_id = data.split("character_count:")[1]

    try:
        result = await user_collection.aggregate([
            {"$match": {"characters.id": char_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.id": char_id}},
            {"$group": {"_id": "$id"}},
            {"$count": "user_count"},
        ]).to_list(length=1)

        user_count = result[0]["user_count"] if result else 0

        if user_count == 0:
            await query.answer("🚫 No users currently own this character.", show_alert=True)
        else:
            await query.answer(f"📊 This character is owned by {user_count} users!", show_alert=True)

    except Exception as e:
        await query.answer(f"❌ An error occurred: {e}", show_alert=True)


# Register handlers — बॉट के startup कोड में इस फाइल को import कर handler लोड करें
application.add_handler(InlineQueryHandler(inlinequery))
application.add_handler(CallbackQueryHandler(guessed_callback, pattern=r"^character_count:.+$"))
