import re
import time
from html import escape
from pyrogram import filters, types, enums
from Grabber import app, collection, user_collection, LOGGER

# Cache
global_guess_cache = {}

async def get_global_guess_count(char_id: str) -> int:
    if char_id in global_guess_cache:
        return global_guess_cache[char_id]
    count = await user_collection.count_documents({'characters.id': char_id})
    global_guess_cache[char_id] = count
    return count

@app.on_inline_query()
async def inline_query_handler(_, query: types.InlineQuery) -> None:
    query_text = query.query.strip()
    
    filter_query = {}
    if query_text:
        # Check if it's a collection request (handled by harem logic usually, but we implement basic search here)
        if query_text.startswith("collection."):
            try:
                user_id = int(query_text.split(".")[1])
                user_doc = await user_collection.find_one({"id": user_id})
                characters = user_doc.get("characters", []) if user_doc else []
                # Pyrogram inline results limit is 50 usually
                unique_chars = {c['id']: c for c in characters}.values()
                results = []
                for character in list(unique_chars)[:50]:
                    results.append(
                        types.InlineQueryResultPhoto(
                            photo_url=character["img_url"],
                            thumb_url=character["img_url"],
                            caption=f"🌸 **{escape(character['name'])}**\n🎬 Anime: {escape(character['anime'])}\n🔮 Rarity: {escape(character['rarity'])}\n🆔 ID: {character['id']}",
                            parse_mode=enums.ParseMode.MARKDOWN
                        )
                    )
                await query.answer(results, cache_time=5)
                return
            except Exception as e:
                LOGGER.error(f"Error in collection inline query: {e}")
        
        # Normal search
        regex = re.compile(re.escape(query_text), re.IGNORECASE)
        filter_query = {"$or": [{"name": regex}, {"anime": regex}]}
    
    # DB search
    cursor = collection.find(filter_query, {
        "id": 1, "name":1, "anime":1, "rarity":1, "img_url":1
    }).limit(50)
    characters = await cursor.to_list(length=50)

    results = []
    for character in characters:
        char_id = str(character["id"])
        name = escape(character["name"])
        anime = escape(character["anime"])
        rarity = escape(character["rarity"])

        caption = (
            f"🌸 **{name}**\n"
            f"🎬 **Anime:** {anime}\n"
            f"🔮 **Rarity:** {rarity}\n"
            f"🆔 **ID:** `{char_id}`"
        )

        keyboard = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("📊 How many users have?", callback_data=f"character_count:{char_id}")]
        ])

        results.append(
            types.InlineQueryResultPhoto(
                photo_url=character["img_url"],
                thumb_url=character["img_url"],
                caption=caption,
                parse_mode=enums.ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        )

    await query.answer(results, cache_time=5)

@app.on_callback_query(filters.regex(r"^character_count:.+$"))
async def guessed_callback(_, query: types.CallbackQuery) -> None:
    char_id = query.data.split("character_count:")[1]

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
        LOGGER.error(f"Error in guessed_callback: {e}")
        await query.answer(f"❌ An error occurred.", show_alert=True)
