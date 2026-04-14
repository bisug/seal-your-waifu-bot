from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape as escape
from Grabber import app, collection, LOGGER

@app.on_message(filters.command("sips"))
async def search_character(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide a name to search for.")

    name_to_search = " ".join(message.command[1:]).strip()
    
    # Use .limit(21) to avoid loading massive results into memory
    characters_cursor = collection.find(
        {"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}}
    ).limit(21)

    found_characters = await characters_cursor.to_list(length=21)

    if not found_characters:
        return await message.reply_text("No characters found with that name.")

    response_message = "<b>🔍 Found Characters:</b>\n\n"
    # Show only the first 20
    for character in found_characters[:20]:
        response_message += f"🆔 <code>ID: {character['id']}</code>\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"

    # If we found more than 20 (indicated by our 21st result)
    if len(found_characters) > 20:
        total_estimate = await collection.count_documents({"name": {"$regex": f".*{name_to_search}.*", "$options": "i"}})
        response_message += f"<i>...and {total_estimate - 20} more.</i>"

    await message.reply_text(response_message, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("sani"))
async def search_anime(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide an anime title to search for.")

    anime_title = " ".join(message.command[1:]).strip()

    # Use .limit(21) for memory efficiency
    characters_cursor = collection.find(
        {"anime": {"$regex": f".*{anime_title}.*", "$options": "i"}}
    ).limit(21)

    found_characters = await characters_cursor.to_list(length=21)

    if not found_characters:
        return await message.reply_text(f"No characters found from anime titled '{escape(anime_title)}'.")

    response_message = f"<b>🎬 Characters from Anime '{escape(anime_title)}':</b>\n\n"
    for character in found_characters[:20]:
        response_message += f"🆔 <code>ID: {character['id']}</code>\n"
        response_message += f"📛 Name: {escape(character['name'])}\n"
        response_message += f"🔮 Rarity: {escape(character['rarity'])}\n\n"

    if len(found_characters) > 20:
        total_estimate = await collection.count_documents({"anime": {"$regex": f".*{anime_title}.*", "$options": "i"}})
        response_message += f"<i>...and {total_estimate - 20} more.</i>"

    await message.reply_text(response_message, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("animes"))
async def anime_list(_, message: types.Message):
    try:
        anime_names = await collection.distinct("anime")
        if not anime_names:
            return await message.reply_text("No anime found in the database.")

        sorted_animes = sorted(anime_names)
        anime_lines = [f"• {escape(anime)}" for anime in sorted_animes]
        
        # Build the list and truncate safely if it exceeds Telegram limits
        final_list = ""
        for line in anime_lines:
            if len(final_list) + len(line) + 20 > 4000:
                final_list += "\n<i>...and others (truncated)</i>"
                break
            final_list += line + "\n"

        await message.reply_text(
            f"📜 <b>Anime List in Database:</b>\n\n{final_list}",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LOGGER.error(f"Error in anime_list: {e}")
        await message.reply_text(f"Error fetching anime list: {str(e)}")
