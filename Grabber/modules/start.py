from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER
from Grabber.database import total_pm_users

LOGGER.info("Loading Start module...")

START_TEXT = """
***Hey! I'm Seal... Your ultimate Character Catcher!*** ✨

Add me to your groups and I'll drop random characters periodically. 
Guess their names to build your massive harem!

🦋 /harem - View your collection
⚔ /battle - Fight others for coins
🛍 /shop - Buy special characters
"""

HELP_TEXT = """
***Complete Command List:***

🔹 /seal <name> - Catch a dropped character
🔹 /harem - Your collection
🔹 /top - Global rankings
🔹 /ctop - Chat rankings
🔹 /battle - Bet & Fight
🔹 /trade - Exchange characters
🔹 /gift - Send characters to friends
🔹 /hunt - Find eggs with pets
🔹 /hatch - Hatch eggs for characters
"""

@app.on_message(filters.command("start"))
async def start_handler(_, message: types.Message):
    user_id = message.from_user.id
    
    # Track new users
    await total_pm_users.update_one(
        {"_id": user_id},
        {"$set": {"first_name": message.from_user.first_name, "username": message.from_user.username}},
        upsert=True
    )

    if message.chat.type == enums.ChatType.PRIVATE:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("❓ Help", callback_data="st:h"),
             types.InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")],
            [types.InlineKeyboardButton("📢 Updates", url=f"https://t.me/{UPDATE_CHAT}")]
        ])
        
        await message.reply_photo(
            photo=random_photo(),
            caption=START_TEXT,
            reply_markup=markup,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("✅ I'm active and ready to drop characters!")

@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    action = query.data.split(":")[1]
    
    if action == "h":
        markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("⤾ Back", callback_data="st:b")]])
        await query.message.edit_caption(HELP_TEXT, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
    else:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("❓ Help", callback_data="st:h"),
             types.InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")],
            [types.InlineKeyboardButton("📢 Updates", url=f"https://t.me/{UPDATE_CHAT}")]
        ])
        await query.message.edit_caption(START_TEXT, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
    
    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)
