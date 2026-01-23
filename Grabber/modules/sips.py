from pyrogram import filters, types, enums
from html import escape
from Grabber import app, collection, LOGGER

@app.on_message(filters.command("sips"))
async def search_character(_, message: types.Message):
    # Get the name to search for from the command arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a name to search for.")
        return

    name_to_search = " ".join(message.command[1:]).strip()

    # Search for characters by name in the total collection
    characters_cursor = collection.find({"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}})

    found_characters = []
    async for character in characters_cursor:
        found_characters.append(character)

    if not found_characters:
        await message.reply_text("No characters found with that name.")
        return

    # Prepare the response message with found characters
    response_message = "<b>🔍 Found Characters:</b>\n\n"
    for character in found_characters[:20]: # Limit for performance and message size
        response_message += f"🆔 `ID: {character['id']}`\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"

    if len(found_characters) > 20:
        response_message += f"<i>...and {len(found_characters) - 20} more.</i>"

    await message.reply_text(response_message, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("sani"))
async def search_anime(_, message: types.Message):
    # Get the anime title to search for from the command arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide an anime title to search for.")
        return

    anime_title = " ".join(message.command[1:]).strip()

    # Search for characters by anime title in the total collection
    characters_cursor = collection.find({"anime": {"$regex": f".*{anime_title}.*", "$options": "i"}})

    found_characters = []
    async for character in characters_cursor:
        found_characters.append(character)

    if not found_characters:
        await message.reply_text(f"No characters found from anime titled '{anime_title}'.")
        return

    # Prepare the response message with found characters
    response_message = f"<b>🎬 Characters from Anime '{escape(anime_title)}':</b>\n\n"
    for character in found_characters[:20]:
        response_message += f"🆔 `ID: {character['id']}`\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"

    if len(found_characters) > 20:
        response_message += f"<i>...and {len(found_characters) - 20} more.</i>"

    await message.reply_text(response_message, parse_mode=enums.ParseMode.HTML)
