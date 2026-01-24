from html import escape
from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER
from Grabber.database import total_pm_users

LOGGER.info("Loading Start module...")

START_TEXT = """
<b>✨ Welcome to {bot_name}! ✨</b>

<b>Hey {first_name}!</b> I am your ultimate companion for <b>Character Catching & PvP Battles!</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>🔥 Core Features:</b>
🌸 <b>Catch</b> rare anime characters.
⚔️ <b>Battle</b> other players with your characters.
🐣 <b>Hatch</b> eggs and grow your collection.
🎫 <b>Progress</b> through the Battle Pass!
━━━━━━━━━━━━━━━━━━━━━━━━

<i>Add me to your group and start your journey today!</i>
"""

# Help Categories
HELP_DATA = {
    "MAIN": {
        "text": "<b>📚 Seal Bot - Help Menu</b>\n\nSelect a category below to see available commands:",
        "buttons": [
            [types.InlineKeyboardButton("🎮 Core Basics", callback_data="help:core"),
             types.InlineKeyboardButton("🐾 Pet System", callback_data="help:pet")],
            [types.InlineKeyboardButton("⚔️ Battle & Coins", callback_data="help:battle"),
             types.InlineKeyboardButton("🎫 Battle Pass", callback_data="help:progression")],
            [types.InlineKeyboardButton("ℹ️ Info & Stats", callback_data="help:info")],
            [types.InlineKeyboardButton("⤾ Main Menu", callback_data="st:b")]
        ]
    },
    "CORE": {
        "text": """
<b>🎮 Core Commands</b>

🔹 <code>/seal &lt;name&gt;</code> - Catch a spawned character
🔹 <code>/harem</code> - View your character collection
🔹 <code>/fav &lt;id&gt;</code> - Set a favorite character
🔹 <code>/trade &lt;my_id&gt; &lt;their_id&gt;</code> - Trade with others
🔹 <code>/gift &lt;id&gt;</code> - Gift a character to a user
""",
    },
    "PET": {
        "text": """
<b>🐾 Pet System</b>

🔹 <code>/petshop</code> - Buy powerful pets
🔹 <code>/mypet</code> - Manage active pet & view stats
🔹 <code>/hunt</code> - Send pet to find loot & XP
🔹 <code>/eggs</code> - Check your egg inventory
🔹 <code>/hatch</code> - Hatch eggs for characters
""",
    },
    "BATTLE": {
        "text": """
<b>⚔️ Battle & Economy</b>

🔹 <code>/battle &lt;amount&gt;</code> - PvP duel (Pets boost win rate!)
🔹 <code>/balance</code> - Check your coins
🔹 <code>/shop</code> - Buy premium characters
🔹 <code>/daily</code> - Claim daily rewards
🔹 <code>/top</code> - Global leaderboard
""",
    },
    "INFO": {
        "text": """
<b>ℹ️ Info & Stats</b>

🔹 <code>/stats</code> - Global bot statistics
🔹 <code>/rarities</code> - Character counts by rarity
🔹 <code>/ping</code> - Real-time system status
🔹 <code>/help</code> - Show this interactive menu
""",
    },
    "PROGRESSION": {
        "text": """
<b>🎫 Battle Pass & Progression</b>

🔹 <code>/pass</code> - View your Battle Pass (Free/Premium/Elite)
🔹 <code>/level</code> - Quick level & XP check
🔹 <code>/quests</code> - View & claim daily quests

<i>💡 Gain XP by catching, battling, and hatching!</i>
<i>🎁 Unlock rewards at levels 5, 10, 25, and 50</i>
""",
    }
}

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
            [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
             types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
            [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
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

# Handle Start Menu & Back
@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    action = query.data.split(":")[1]
    
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
            types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
        [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
    ])
    
    first_name = escape(query.from_user.first_name)
    text = START_TEXT.format(first_name=first_name, bot_name=app.name)
    
    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass
    
    await query.answer()

# Handle Interactive Help
@app.on_callback_query(filters.regex(r"^help:(.+)"))
async def help_callback_handler(_, query: types.CallbackQuery):
    module = query.data.split(":")[1].upper()
    
    if module == "MAIN":
        data = HELP_DATA["MAIN"]
        markup = types.InlineKeyboardMarkup(data["buttons"])
        text = data["text"]
    elif module in HELP_DATA:
        text = HELP_DATA[module]["text"]
        markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("⤾ Back to Help", callback_data="help:main")]])
    else:
        await query.answer("❌ Menu not found.", show_alert=True)
        return

    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass
    
    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)
