import re
from html import escape
from pyrogram import filters, types, enums, errors
from Grabber import app, collection, user_collection, LOGGER

# Constants
RESULTS_PER_PAGE = 50

# ─── Inline Query Handler ───────────────────────────────────────────────────
@app.on_inline_query()
async def inline_query_handler(_, query: types.InlineQuery) -> None:
    query_text = query.query.strip()
    offset = int(query.offset) if query.offset else 0
    results = []
    
    # Context for pagination (collection.<id> vs global)
    # We will pass this minimal context in callback data
    search_context = "global" 
    
    # ─── Collection Search ─────────────────────────────────────────────────
    if query_text.startswith("collection."):
        try:
            parts = query_text.split(".")
            if len(parts) < 2:
                return await query.answer([], cache_time=1)
            
            user_id = int(parts[1])
            search_context = f"col_{user_id}"
            
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
            
            # Pack results with gallery markup
            for i, char in enumerate(characters):
                neighbors = get_neighbors(characters, i)
                res = create_inline_result(char, neighbors, offset, search_context)
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
        search_context = f"q_{query_text[:10]}" # Short hash context
        filter_query = {
            "$or": [
                {"name": {"$regex": query_text, "$options": "i"}},
                {"anime": {"$regex": query_text, "$options": "i"}}
            ]
        }

    # Fetch with ascending ID sort and pagination
    cursor = collection.find(filter_query).sort("id", 1).skip(offset).limit(RESULTS_PER_PAGE)
    characters = await cursor.to_list(length=RESULTS_PER_PAGE)

    for i, char in enumerate(characters):
        neighbors = get_neighbors(characters, i)
        res = create_inline_result(char, neighbors, offset, search_context)
        if res: results.append(res)

    next_offset = str(offset + RESULTS_PER_PAGE) if len(characters) == RESULTS_PER_PAGE else ""
    await query.answer(results, cache_time=1, next_offset=next_offset)


# ─── Helpers ───────────────────────────────────────────────────────────────
def get_neighbors(char_list, index):
    """Get 4 surrounding characters for the navigation grid."""
    start = max(0, index - 2)
    end = min(len(char_list), index + 3)
    return char_list[start:end]

def create_gallery_keyboard(current_char_id, neighbors, offset, context):
    """Generate the keyboard with only the Owners Count button."""
    buttons = [
        [types.InlineKeyboardButton("📊 Owners Count", callback_data=f"character_count:{current_char_id}")]
    ]
    return types.InlineKeyboardMarkup(buttons)

def create_inline_result(character: dict, neighbors: list, offset: int, context: str) -> types.InlineQueryResultPhoto:
    """Create inline result with interactive gallery keyboard attached to the message."""
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
    
    # The message sent to chat will have this keyboard
    reply_markup = create_gallery_keyboard(char_id, neighbors, offset, context)

    return types.InlineQueryResultPhoto(
        id=char_id,
        photo_url=img_url,
        thumb_url=img_url,
        title=name,
        description=f"🎬 {anime}\n✨ {rarity} | 🆔 {char_id}",
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )


# ─── Callbacks ─────────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^gal:view:"))
async def gallery_view_callback(_, query: types.CallbackQuery):
    try:
        char_id = query.data.split(":")[2]
        
        # Fetch character details
        character = await collection.find_one({"id": char_id})
        if not character:
            return await query.answer("❌ Character data not found.", show_alert=True)
            
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
        
        # We need to reconstruct neighbors logic ideally, but for now 
        # a simple "Owners" button is enough to prove the concept without heavy context passing
        # or we could pass context via the click if needed.
        buttons = [
            [types.InlineKeyboardButton("📊 Owners Count", callback_data=f"character_count:{char_id}")]
        ]
        
        await query.message.edit_media(
            media=types.InputMediaPhoto(media=img_url, caption=caption, parse_mode=enums.ParseMode.HTML),
            reply_markup=types.InlineKeyboardMarkup(buttons)
        )
        await query.answer()
        
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Gallery View Error: {e}")
        await query.answer("❌ Error loading character.", show_alert=True)

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
