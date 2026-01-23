from pyrogram import filters, types, enums
from Grabber import app, collection, LOGGER

@app.on_message(filters.command("animes"))
async def anime_list(_, message: types.Message) -> None:
    """Shows a list of all unique anime names from uploaded waifus."""
    try:
        # Fetch distinct anime names from the database
        anime_names = await collection.distinct("anime")

        if not anime_names:
            await message.reply_text("No anime found in the database.")
            return

        # Format the list for better readability
        anime_list_text = "\n".join(f"• {anime}" for anime in sorted(anime_names))

        # Check for message length limits (4096 characters)
        if len(anime_list_text) > 4000:
            # If too long, send first part only or ideally split. For now, we truncate.
            anime_list_text = anime_list_text[:4000] + "\n...(truncated)"

        await message.reply_text(
            f"📜 **Anime List in Database:**\n\n{anime_list_text}",
            parse_mode=enums.ParseMode.MARKDOWN
        )

    except Exception as e:
        LOGGER.error(f"Error in anime_list: {e}")
        await message.reply_text(f"Error fetching anime list: {str(e)}")
