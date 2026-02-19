from pyrogram import filters, types, enums, errors
from Grabber.core.utils import md_escape
from Grabber.app import app
from Grabber import PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER
from Grabber.database import total_pm_users
from Grabber import user_collection
from Grabber.modules.pet import DEFAULT_PET
from Grabber.core.progression import add_xp
from Grabber.modules.achievements import check_achievements

LOGGER.info("Loading Start module...")

START_TEXT = """
**✨ Welcome to {bot_name}! ✨**

**Hey {first_name}!** 👋
I’m your ultimate companion for **Anime Character Collecting & PvP Battles!**

━━━━━━━━━━━━━━━━━━━━━━━━
**🔥 What can I do?**
🌸 **Catch** thousands of anime characters.
⚔️ **Battle** friends in strategic duels.
🐣 **Hatch** eggs & raise powerful pets.
🎫 **Rank Up** & unlock exclusive rewards.
🏰 **Build** your Harem & dominate the leaderboard!
━━━━━━━━━━━━━━━━━━━━━━━━

_Add me to your group & start your adventure!_ 🚀
"""

                 
HELP_DATA = {
    "MAIN": {
        "text": "**📚 Seal Bot - Help Menu**\n\nSelect a category below to see available commands:",
        "buttons": [
            [types.InlineKeyboardButton("🎮 Core Basics", callback_data="help:core"),
             types.InlineKeyboardButton("🐾 Pet System", callback_data="help:pet")],
            [types.InlineKeyboardButton("⚔️ Battle & Economy", callback_data="help:battle"),
             types.InlineKeyboardButton("🎫 Progression", callback_data="help:progression")],
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
🔹 `/trade <user> <amount>` - Trade characters/items
🔹 `/gift <id>` - Gift a character to a user
🔹 `/quiz` - Test your anime knowledge & have fun!
""",
    },
    "PET": {
        "text": """
**🐾 Pet System**

🔹 `/petshop` - Buy powerful pets with unique stats
🔹 `/mypet` - Manage active pet & view stats
🔹 `/hunt` - Send pet to find loot, Shards & eggs
🔹 `/eggs` - Manage and hatch your eggs
""",
    },
    "BATTLE": {
        "text": """
**⚔️ Battle & Economy**

🔹 `/battle <amount>` - PvP duel (Turn-based strategy!)
🔹 `/balance` - Check your Shards & Zenith
🔹 `/shop` - Universal Shop Hub (Chars, Pets, Items)
🔹 `/daily` - Claim daily rewards (Streaks!)
🔹 `/weekly` - Claim weekly bonus (Every 7 days)
🔹 `/top` - Global leaderboard (Harem, Shards, Level)
""",
    },
    "INFO": {
        "text": """
**ℹ️ Info & Stats**

🔹 `/stats` - Global bot statistics
🔹 `/rarities` - Character counts by rarity
🔹 `/ctop` - Top chat members (Chat Leaderboard)
🔹 `/ping` - Real-time system status
🔹 `/help` - Show this interactive menu
""",
    },
    "PROGRESSION": {
        "text": """
**🎫 Battle Pass & Progression**

🔹 `/pass` - View your Battle Pass (Free/Premium/Elite)
🔹 `/quests` - Daily & Weekly Quests (Earn XP!)
🔹 `/referrals` - Invite friends & earn rewards
🔹 `/achievements` - View lifetime milestones & titles
🔹 `/level` - Check your level progress

_💡 Gain XP by catching, battling, and completing quests!_
_🎁 Unlock rewards at levels 5, 10, 25, and 50_
""",
    }
}

@app.on_message(filters.command("start"))
async def start_handler(_, message: types.Message):
    user_id = message.from_user.id
    
                                 
                                                                 
    existing_user = await user_collection.find_one({"id": user_id})
    
    await total_pm_users.update_one(
        {"_id": user_id},
        {"$set": {"first_name": message.from_user.first_name, "username": message.from_user.username}},
        upsert=True
    )
    
                    
    if len(message.command) > 1:
        param = message.command[1]
        
                                             
        if param.startswith("locate_"):
            try:
                char_id = param.split("_")[1]
                from Grabber.database import collection
                character = await collection.find_one({'id': char_id})
                
                if character:
                    response_message = (
                        f"**Character Name:** {character['name']}\n"
                        f"**Anime:** {character['anime']}\n"
                        f"**Rarity:** {character['rarity']}\n"
                        f"**Character ID:** `{character['id']}`\n"
                    )

                    await message.reply_photo(
                        photo=character['img_url'],
                        caption=response_message,
                        parse_mode=enums.ParseMode.MARKDOWN
                    )
                    return                                        
                else:
                    await message.reply_text("❌ Character not found.")
                    return
            except Exception as e:
                LOGGER.error(f"Locate Error: {e}")
                pass

        elif not existing_user and param.startswith("ref_"):
            try:
                referrer_id = int(param.split("_")[1])
                if referrer_id != user_id:
                                   
                                                                 
                    upgraded_pet = DEFAULT_PET.copy()
                    upgraded_pet["level"] = 10
                    upgraded_pet["hp"] += 45                          
                    upgraded_pet["atk"] += 18
                    upgraded_pet["spd"] += 9
                    
                    await user_collection.update_one(
                        {"id": user_id},
                        {
                            "$set": {
                                "balance": 1500,
                                "pets": [upgraded_pet],
                                "current_pet": upgraded_pet["name"],
                                "referred_by": referrer_id
                            }
                        },
                        upsert=True
                    )
                    
                                       
                    await user_collection.update_one(
                        {"id": referrer_id},
                        {
                            "$inc": {"balance": 500, "referrals_count": 1, "referrals_earned": 500}
                        }
                    )
                    await add_xp(referrer_id, 50, "referral")
                    await check_achievements(referrer_id)
                    
                                    
                    try:
                        await app.send_message(
                            referrer_id,
                            f"🎉 **New Referral!**\n\n{md_escape(message.from_user.first_name)} joined using your link.\n+500 ⬪ | +50 XP"
                        )
                    except:
                        pass
                        
                    await message.reply_text("🎁 **Welcome Bonus!**\nYou received **1,500 ⬪** and a **Level 10 Pet** for using a referral link! 🚀")
                    
            except ValueError:
                pass


    if message.chat.type == enums.ChatType.PRIVATE:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
             types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
            [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
        ])
        
        first_name = md_escape(message.from_user.first_name)
        from Grabber import BOT_NAME
        text = START_TEXT.format(first_name=first_name, bot_name=BOT_NAME)

        await message.reply_photo(
            photo=random_photo(),
            caption=text,
            reply_markup=markup
        )
    else:
        await message.reply_text("✅ **I'm active and ready to drop characters!**")

                          
@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    action = query.data.split(":")[1]
    
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
            types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
        [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
    ])
    
    first_name = md_escape(query.from_user.first_name)
    from Grabber import BOT_NAME
    text = START_TEXT.format(first_name=first_name, bot_name=BOT_NAME)
    
    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup)
        else:
            await query.message.edit_text(text, reply_markup=markup)
    except errors.MessageNotModified:
        pass
    
    await query.answer()

                         
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
            await query.message.edit_caption(text, reply_markup=markup)
        else:
            await query.message.edit_text(text, reply_markup=markup)
    except errors.MessageNotModified:
        pass
    
    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)
