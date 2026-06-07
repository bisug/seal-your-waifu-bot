import hashlib
from collections import OrderedDict
from pyrogram import enums, errors, filters, types

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Grabber import LOGGER, app, collection
from Grabber.core.cache import rget, rset
from Grabber.core.character_search import build_character_search_filter
from Grabber.core.utils import handle_errors, html_escape as escape
# --- PAGINATION HELPERS ---
_MAX_SEARCH_FALLBACK = 1000
_search_fallback: OrderedDict[str, str] = OrderedDict()


def _remember_search(query_id: str, query: str):
    _search_fallback[query_id] = query
    _search_fallback.move_to_end(query_id)
    while len(_search_fallback) > _MAX_SEARCH_FALLBACK:
        _search_fallback.popitem(last=False)


async def get_search_results_page(query, search_type, page=1):
    """
    Common helper to fetch a page of search results and generate the message + buttons.
    search_type: 'all', 'name', 'anime', or 'id'
    """
    limit = 20
    skip = (page - 1) * limit
    field_map = {
        "all": None,
        "name": ("name",),
        "anime": ("anime",),
        "id": ("id",),
    }
    search_filter = build_character_search_filter(query, fields=field_map.get(search_type))
    if not search_filter:
        return None, None

    # 1. Fetch matching documents
    cursor = collection.find(search_filter).skip(skip).limit(limit + 1)
    found_characters = await cursor.to_list(length=limit + 1)
    if not found_characters and page == 1:
        return None, None
    # 2. Format the Text Block
    if search_type == "anime":
        header = f"🎬 <b>Characters from '{escape(query)}'</b>"
    elif search_type == "id":
        header = f"🆔 <b>Character ID Search: {escape(query)}</b>"
    else:
        header = f"🔍 <b>Character Search: {escape(query)}</b>"
    response_message = f"{header}\n<i>Page: {page}</i>\n\n"
    for character in found_characters[:limit]:
        response_message += f"🆔 <code>ID: {character['id']}</code>\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        response_message += f"🎬 Series: {escape(character['anime'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"
    # 3. Generate Buttons
    buttons = []
    # Check if we have a next page (using our limit+1 fetch)
    has_next = len(found_characters) > limit
    # Manage Callback Data Session (Telegram 64-byte limit)
    # Prefix: sc:{type_idx}:{page}:{query_id}
    type_map = {"all": "0", "name": "1", "anime": "2", "id": "3"}
    type_idx = type_map.get(search_type, "0")
    # If query is too long, store in Redis
    if len(query) > 30 or ":" in query:
        query_id = hashlib.md5(query.encode()).hexdigest()[:10]
        await rset(f"search:{query_id}", query, 3600)
        _remember_search(query_id, query)
    else:
        query_id = query
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"sc:{type_idx}:{page-1}:{query_id}"))
    if has_next:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"sc:{type_idx}:{page+1}:{query_id}"))
    if nav_row:
        buttons.append(nav_row)
    return response_message, InlineKeyboardMarkup(buttons)
@app.on_message(filters.command("sips"))
@handle_errors
async def search_character(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide a name, character ID, or anime title to search for.")
    query = " ".join(message.command[1:]).strip()
    text, buttons = await get_search_results_page(query, "all", 1)
    if not text:
        return await message.reply_text("No characters found for that search.")
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("sani"))
@handle_errors
async def search_anime(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide an anime title to search for.")
    query = " ".join(message.command[1:]).strip()
    text, buttons = await get_search_results_page(query, "anime", 1)
    if not text:
        return await message.reply_text(f"No characters found from anime titled '{escape(query)}'.")
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
@app.on_callback_query(filters.regex(r"^sc:"))
async def search_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":", 3)
    type_idx = data[1]
    page = int(data[2])
    query_id = data[3]
    search_type = {"0": "all", "1": "name", "2": "anime", "3": "id"}.get(type_idx, "all")
    # Retrieve query from Redis if it looks like a hash
    if len(query_id) == 10:
        search_query = await rget(f"search:{query_id}") or _search_fallback.get(query_id)
        if not search_query:
            return await query.answer("⌛ Search session expired! Please search again.", show_alert=True)
    else:
        search_query = query_id
    text, buttons = await get_search_results_page(search_query, search_type, page)
    if text:
        try:
            await query.message.edit_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
    await query.answer()
@app.on_message(filters.command("animes"))
@handle_errors
async def anime_list(_, message: types.Message):
    try:
        anime_names = await collection.distinct("anime")
        if not anime_names:
            return await message.reply_text("No anime found in the database.")
        sorted_animes = sorted(anime_names)
        anime_lines = [f"• {escape(anime)}" for anime in sorted_animes]
        final_list = ""
        for line in anime_lines:
            if len(final_list) + len(line) + 20 > 4000:
                final_list += "\n<i>...and others (truncated)</i>"
                break
            final_list += line + "\n"
        await message.reply_text(
            f"📜 <b>Anime List in Database:</b>\n\n{final_list}",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Error in anime_list: {e}")
        await message.reply_text(f"Error fetching anime list: {str(e)}")
