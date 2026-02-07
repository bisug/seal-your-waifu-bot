from html import escape
from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER
from Grabber.database import total_pm_users

LOGGER.info("Loading Start module...")

START_TEXT = """
**✨ Welcome to {bot_name}! ✨**

**Hey {first_name}!** I am your ultimate companion for **Character Catching & PvP Battles!**

━━━━━━━━━━━━━━━━━━━━━━━━
**🔥 Core Features:**
🌸 **Catch** rare anime characters.
⚔️ **Battle** other players with your characters.
🐣 **Hatch** eggs and grow your collection.
🎫 **Progress** through the Battle Pass!
━━━━━━━━━━━━━━━━━━━━━━━━

_Add me to your group and start your journey today!_
"""

# Help Categories
HELP_DATA = {
    "MAIN": {
        "text": "**📚 Seal Bot - Help Menu**\n\nSelect a category below to see available commands:",
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
**🎮 Core Commands**

🔹 `/seal <name>` - Catch a spawned character
🔹 `/harem` - View your character collection
🔹 `/fav <id>` - Set a favorite character
🔹 `/trade <my_id> <their_id>` - Trade with others
🔹 `/gift <id>` - Gift a character to a user
""",
    },
    "PET": {
        "text": """
**🐾 Pet System**

🔹 `/petshop` - Buy powerful pets
🔹 `/mypet` - Manage active pet & view stats
🔹 `/hunt` - Send pet to find loot & XP
🔹 `/eggs` - Check your egg inventory
🔹 `/hatch` - Hatch eggs for characters
""",
    },
    "BATTLE": {
        "text": """
**⚔️ Battle & Economy**

🔹 `/battle <amount>` - PvP duel (Pets boost win rate!)
🔹 `/balance` - Check your coins
🔹 `/shop` - Buy premium characters
🔹 `/daily` - Claim daily rewards
🔹 `/top` - Global leaderboard
""",
    },
    "INFO": {
        "text": """
**ℹ️ Info & Stats**

🔹 `/stats` - Global bot statistics
🔹 `/rarities` - Character counts by rarity
🔹 `/ping` - Real-time system status
🔹 `/help` - Show this interactive menu
""",
    },
    "PROGRESSION": {
        "text": """
**🎫 Battle Pass & Progression**

🔹 `/pass` - View your Battle Pass (Free/Premium/Elite)
🔹 `/level` - Quick level & XP check
🔹 `/quests` - View & claim daily quests

_💡 Gain XP by catching, battling, and hatching!_
_🎁 Unlock rewards at levels 5, 10, 25, and 50_
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
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("✅ **I'm active and ready to drop characters!**", parse_mode=enums.ParseMode.MARKDOWN)

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
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
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
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
    except errors.MessageNotModified:
        pass
    
    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)
