import hashlib
from collections import OrderedDict
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Grabber import LOGGER, app, collection
from Grabber.core.cache import rget, rset
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
    search_type: 'name' or 'anime'
    """
    limit = 20
    skip = (page - 1) * limit
    # 1. Fetch matching documents
    cursor = collection.find({search_type: {"$regex": f".*{query}.*", "$options": "i"}}).skip(skip).limit(limit + 1)
    found_characters = await cursor.to_list(length=limit + 1)
    if not found_characters and page == 1:
        return None, None
    # 2. Format the Text Block
    header = "🔍 <b>Character Search</b>" if search_type == 'name' else f"🎬 <b>Characters from '{escape(query)}'</b>"
    response_message = f"{header}\n<i>Page: {page}</i>\n\n"
    for character in found_characters[:limit]:
        response_message += f"🆔 <code>ID: {character['id']}</code>\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        if search_type == 'name':
             response_message += f"🎬 Series: {escape(character['anime'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"
    # 3. Generate Buttons
    buttons = []
    # Check if we have a next page (using our limit+1 fetch)
    has_next = len(found_characters) > limit
    # Manage Callback Data Session (Telegram 64-byte limit)
    # Prefix: sc:{type_idx}:{page}:{query_id}
    type_idx = "1" if search_type == "name" else "2"
    # If query is too long, store in Redis
    if len(query) > 30:
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
        return await message.reply_text("Please provide a name to search for.")
    query = " ".join(message.command[1:]).strip()
    text, buttons = await get_search_results_page(query, "name", 1)
    if not text:
        return await message.reply_text("No characters found with that name.")
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
    data = query.data.split(":")
    type_idx = data[1]
    page = int(data[2])
    query_id = data[3]
    search_type = "name" if type_idx == "1" else "anime"
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
