from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, BOT_USERNAME

@app.on_message(filters.command("search"))
async def search_waifu(_, message: types.Message):
                                                            
    keyboard = [
        [types.InlineKeyboardButton("🔍 Search Waifu", switch_inline_query_current_chat="")]
    ]
    reply_markup = types.InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "🪄 To search for a waifu, click the button below!",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
