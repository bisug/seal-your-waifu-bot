from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, collection

async def anime_list(update: Update, context: CallbackContext) -> None:
    """Shows a list of all unique anime names from uploaded waifus."""
    try:
        # Fetch distinct anime names from the database
        anime_names = await collection.distinct("anime")

        if not anime_names:
            await update.message.reply_text("No anime found in the database.")
            return

        # Format the list for better readability
        anime_list_text = "\n".join(f"• {anime}" for anime in sorted(anime_names))

        await update.message.reply_text(
            f"📜 Anime List in Database:\n\n{anime_list_text}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"Error fetching anime list: {str(e)}")

# Add the handler for the /anime command
ANIME_HANDLER = CommandHandler("animes", anime_list, block=False)
print("✅ /anime command registered")

application.add_handler(ANIME_HANDLER)
