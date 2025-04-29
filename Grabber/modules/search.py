from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from Grabber import application
from telegram import Update
from telegram.ext import ContextTypes

async def search_waifu(update: Update, context: ContextTypes):
    """Handles the /search command with an inline button."""
    keyboard = [
        [InlineKeyboardButton("🔍 Search Waifu", switch_inline_query="@Seal_Your_Waifu_Bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🪄 To search for a waifu, click the button below!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Adding command handler
application.add_handler(CommandHandler("search", search_waifu, block=False))
