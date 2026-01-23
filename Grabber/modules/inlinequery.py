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
                return await query.answer([], cache_time=1)
            
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
                {"$sort": {"id": 1}},
                {"$skip": offset},
                {"$limit": RESULTS_PER_PAGE}
            ]
            
            characters = await user_collection.aggregate(pipeline).to_list(length=RESULTS_PER_PAGE)
            
            for char in characters:
                res = create_inline_result(char)
                if res: results.append(res)
                
            next_offset = str(offset + RESULTS_PER_PAGE) if len(characters) == RESULTS_PER_PAGE else ""
            await query.answer(results, cache_time=1, next_offset=next_offset)
            return

        except (ValueError, IndexError):
            return await query.answer([], cache_time=1)
        except Exception as e:
            LOGGER.error(f"Inline collection error: {e}")
            return await query.answer([], cache_time=1)

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

    # Fetch with ascending ID sort and pagination
    cursor = collection.find(filter_query).sort("id", 1).skip(offset).limit(RESULTS_PER_PAGE)
    characters = await cursor.to_list(length=RESULTS_PER_PAGE)

    for char in characters:
        res = create_inline_result(char)
        if res: results.append(res)

    next_offset = str(offset + RESULTS_PER_PAGE) if len(characters) == RESULTS_PER_PAGE else ""
    await query.answer(results, cache_time=1, next_offset=next_offset)

def create_inline_result(character: dict) -> types.InlineQueryResultPhoto:
    """Standardized helper to create inline results with HTML formatting."""
    if not character.get("img_url"):
        return None

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

    return types.InlineQueryResultPhoto(
        id=char_id,
        photo_url=img_url,
        thumb_url=img_url,
        caption=caption,
        parse_mode=enums.ParseMode.HTML
    )

