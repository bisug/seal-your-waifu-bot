from html import escape
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER
from Grabber.database import total_pm_users

LOGGER.info("Loading Start module...")

START_TEXT = """
<b>Hey, {first_name}! I’m {bot_name} — your ultimate Character Catcher!</b> ✨

Add me to your groups and I’ll drop random characters from time to time.
Guess their names, catch them first, and build your own massive harem!
"""

HELP_TEXT = """
<b>📚 Seal Bot - Complete Guide</b>

<b>🎮 Core Commands:</b>
🔹 <code>/seal &lt;name&gt;</code> - Catch a spawned character
🔹 <code>/harem</code> - View your character collection
🔹 <code>/fav &lt;id&gt;</code> - Set a favorite character
🔹 <code>/trade &lt;my_id&gt; &lt;their_id&gt;</code> - Trade with others
🔹 <code>/gift &lt;id&gt;</code> - Gift a character to a user

<b>🐾 Pet System:</b>
🔹 <code>/petshop</code> - Buy powerful pets
🔹 <code>/mypet</code> - Manage active pet & view stats
🔹 <code>/hunt</code> - Send pet to find loot & XP
🔹 <code>/eggs</code> - Check your egg inventory
🔹 <code>/hatch</code> - Hatch eggs for characters

<b>⚔️ Battle & Economy:</b>
🔹 <code>/battle &lt;amount&gt;</code> - PvP duel (Pets boost win rate!)
🔹 <code>/balance</code> - Check your coins
🔹 <code>/shop</code> - Buy premium characters
🔹 <code>/daily</code> - Claim daily rewards
🔹 <code>/top</code> - Global leaderboard

<b>ℹ️ Info:</b>
🔹 <code>/stats</code> - Bot statistics
🔹 <code>/ping</code> - Check latency
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
        
        first_name = escape(message.from_user.first_name)
        text = START_TEXT.format(first_name=first_name, bot_name=app.name)

        await message.reply_photo(
            photo=random_photo(),
            caption=text,
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text("✅ <b>I'm active and ready to drop characters!</b>", parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    action = query.data.split(":")[1]
    
    if action == "h":
        markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("⤾ Back", callback_data="st:b")]])
        await query.message.edit_caption(HELP_TEXT, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("❓ Help", callback_data="st:h"),
             types.InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_CHAT}")],
            [types.InlineKeyboardButton("📢 Updates", url=f"https://t.me/{UPDATE_CHAT}")]
        ])
        
        first_name = escape(query.from_user.first_name)
        text = START_TEXT.format(first_name=first_name, bot_name=app.name)
        await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    
    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)
