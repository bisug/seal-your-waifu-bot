import re
from html import escape
from pyrogram import filters, types, enums
from Grabber import app, collection, user_collection, LOGGER

# Constants
RESULTS_PER_PAGE = 50

@app.on_inline_query()
async def inline_query_handler(_, query: types.InlineQuery) -> None:
    query_text = query.query.strip()
    offset = int(query.offset) if query.offset else 0
    results = []
    
    # ─── Collection Search (collection.<user_id>) ───────────────────────────
    if query_text.startswith("collection."):
        try:
            parts = query_text.split(".")
            if len(parts) < 2:
                return await query.answer([], cache_time=5)
            
            user_id = int(parts[1])
            # Optimized aggregation: Get unique characters from user collection sorted by ID desc
            # This is much faster than fetching full user doc and filtering in Python
            pipeline = [
                {"$match": {"id": user_id}},
                {"$unwind": "$characters"},
                {"$replaceRoot": {"newRoot": "$characters"}},
                {"$group": {
                    "_id": "$id",
                    "id": {"$first": "$id"},
                    "name": {"$first": "$name"},
                    "anime": {"$first": "$anime"},
                    "rarity": {"$first": "$rarity"},
                    "img_url": {"$first": "$img_url"}
                }},
                {"$sort": {"id": -1}},
                {"$skip": offset},
                {"$limit": RESULTS_PER_PAGE}
            ]
            
            characters = await user_collection.aggregate(pipeline).to_list(length=RESULTS_PER_PAGE)
            
            for char in characters:
                results.append(create_inline_result(char))
                
            next_offset = str(offset + RESULTS_PER_PAGE) if len(characters) == RESULTS_PER_PAGE else ""
            await query.answer(results, cache_time=5, next_offset=next_offset)
            return

        except (ValueError, IndexError):
            return await query.answer([], cache_time=5)
        except Exception as e:
            LOGGER.error(f"Inline collection error: {e}")
            return await query.answer([], cache_time=5)

    # ─── Global Character Search ───────────────────────────────────────────
    filter_query = {}
    if query_text:
        # Use native MongoDB regex for performance
        filter_query = {
            "$or": [
                {"name": {"$regex": query_text, "$options": "i"}},
                {"anime": {"$regex": query_text, "$options": "i"}}
            ]
        }

    # Fetch with descending ID sort and pagination
    cursor = collection.find(filter_query).sort("id", -1).skip(offset).limit(RESULTS_PER_PAGE)
    characters = await cursor.to_list(length=RESULTS_PER_PAGE)

    for char in characters:
        results.append(create_inline_result(char))

    next_offset = str(offset + RESULTS_PER_PAGE) if len(characters) == RESULTS_PER_PAGE else ""
    await query.answer(results, cache_time=5, next_offset=next_offset)

def create_inline_result(character: dict) -> types.InlineQueryResultPhoto:
    """Standardized helper to create inline results with HTML formatting."""
    char_id = str(character["id"])
    name = escape(character["name"])
    anime = escape(character["anime"])
    rarity = escape(character["rarity"])
    img_url = character["img_url"]

    caption = (
        f"🌸 <b>{name}</b>\n"
        f"🎬 <b>Anime:</b> {anime}\n"
        f"🔮 <b>Rarity:</b> {rarity}\n"
        f"🆔 <b>ID:</b> <code>{char_id}</code>"
    )

    keyboard = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("📊 Owners Count", callback_data=f"character_count:{char_id}")]
    ])

    return types.InlineQueryResultPhoto(
        photo_url=img_url,
        thumb_url=img_url,
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^character_count:.+$"))
async def guessed_callback(_, query: types.CallbackQuery) -> None:
    char_id = query.data.split("character_count:")[1]

    try:
        # Optimized count check with aggregation
        result = await user_collection.aggregate([
            {"$match": {"characters.id": char_id}},
            {"$count": "user_count"}
        ]).to_list(length=1)

        user_count = result[0]["user_count"] if result else 0

        if user_count == 0:
            await query.answer("🚫 No users currently own this character.", show_alert=True)
        else:
            await query.answer(f"📊 This character is owned by {user_count} users!", show_alert=True)

    except Exception as e:
        LOGGER.error(f"Error in guessed_callback: {e}")
        await query.answer("❌ An error occurred while fetching stats.", show_alert=True)
