from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app

@app.on_message(filters.command("webapp"))
async def webapp_command(_, message):
    user_id = message.from_user.id
                                                                   
                                                       
    web_app_url = f"https://sealbotweb-dd92cdbb6105.herokuapp.com/?user_id={user_id}" 
    
    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("🌐 Open Web Gallery", url=web_app_url)
        ]
    ])
    
    await message.reply_text(
        "**Seal Bot Web Gallery**\n\n"
        "Click the button below to view the full character gallery and your collection!",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
