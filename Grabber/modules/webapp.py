from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app

@app.on_message(filters.command("webapp"))
async def webapp_command(_, message):
    user_id = message.from_user.id


    # Replace with your Heroku domain
    web_app_url = "https://your-heroku-app.herokuapp.com/"

    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("Open Mini App", web_app=types.WebAppInfo(url=web_app_url))
        ]
    ])

    await message.reply_text(
        "<b>Seal Bot Web Gallery</b>\n\n"
        "Click the button below to view the full character gallery and your collection!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
