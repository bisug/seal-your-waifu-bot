from pyrogram import enums, filters, types, errors
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, PHOTO_URL, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT, LOGGER, WEB_APP_URL, BOT_NAME, user_collection
from Grabber.database import total_pm_users, collection
from Grabber.modules.progression.pet import DEFAULT_PET
from Grabber.core.progression import add_xp
from Grabber.modules.progression.achievements import check_achievements
from config import config

LOGGER.info("Loading Start module...")

START_TEXT = """
<b>✨ Welcome to {bot_name}! ✨</b>

<b>Hey {first_name}!</b> 👋
I’m your ultimate companion for <b>Anime Character Collecting & PvP Battles!</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>🔥 What can I do?</b>
🌸 <b>Catch</b> thousands of anime characters.
⚔️ <b>Battle</b> friends in strategic duels.
🐣 <b>Hatch</b> eggs & raise powerful pets.
🎫 <b>Rank Up</b> & unlock exclusive rewards.
🏰 <b>Build</b> your Harem & dominate the leaderboard!
━━━━━━━━━━━━━━━━━━━━━━━━

<i>Add me to your group & start your adventure!</i> 🚀
"""


HELP_DATA = {
    "MAIN": {
        "text": "<b>📚 Seal Bot - Help Menu</b>\n\nSelect a category below to see available commands:",
        "buttons": [
            [types.InlineKeyboardButton("🎮 Core Basics", callback_data="help:core"),
             types.InlineKeyboardButton("🐾 Pet System", callback_data="help:pet")],
            [types.InlineKeyboardButton("⚔️ Battle & Economy", callback_data="help:battle"),
             types.InlineKeyboardButton("🎫 Progression", callback_data="help:progression")],
            [types.InlineKeyboardButton("ℹ️ Info & Stats", callback_data="help:info"),
             types.InlineKeyboardButton("🛠 Admin Tools", callback_data="help:owner")],
            [types.InlineKeyboardButton("⤾ Main Menu", callback_data="st:b")]
        ]
    },
    "CORE": {
        "text": """
<b>🎮 Core Commands</b>

🔹 <code>/nguess</code> - Start an anime character name guessing game
🔹 <code>/seal &lt;name&gt;</code> - Catch a spawned character
🔹 <code>/harem</code> - View your character collection
🔹 <code>/fav &lt;id&gt;</code> - Set a favorite character
🔹 <code>/trade &lt;user&gt; &lt;amount&gt;</code> - Trade characters/items
🔹 <code>/gift &lt;id&gt;</code> - Gift a character to a user
🔹 <code>/quiz</code> - Test your anime knowledge &amp; have fun!
""",
    },
    "PET": {
        "text": """
<b>🐾 Pet System</b>

🔹 <code>/petshop</code> - Buy powerful pets with unique stats
🔹 <code>/mypet</code> - Manage active pet &amp; view stats
🔹 <code>/hunt</code> - Send pet to find loot, Shards &amp; eggs
🔹 <code>/eggs</code> - Manage and hatch your eggs
""",
    },
    "BATTLE": {
        "text": """
<b>⚔️ Battle &amp; Economy</b>

🔹 <code>/battle &lt;amount&gt;</code> - PvP duel (Turn-based strategy!)
🔹 <code>/balance</code> - Check your Shards &amp; Zenith
🔹 <code>/exchange</code> - Convert Shards into Zenith
🔹 <code>/shop</code> - Universal Shop Hub (Chars, Pets, Items)
🔹 <code>/daily</code> - Claim daily rewards (Streaks!)
🔹 <code>/weekly</code> - Claim weekly bonus (Every 7 days)
🔹 <code>/top</code> - Global leaderboard (Harem, Shards, Level)
""",
    },
    "INFO": {
        "text": """
<b>ℹ️ Info &amp; Stats</b>

🔹 <code>/stats</code> - Global bot statistics
🔹 <code>/rarities</code> - Character counts by rarity
🔹 <code>/ctop</code> - Top chat members (Chat Leaderboard)
🔹 <code>/mtop</code> - Global rich leaderboard (Shards)
🔹 <code>/ping</code> - Real-time system status
🔹 <code>/help</code> - Show this interactive menu
""",
    },
    "PROGRESSION": {
        "text": """
<b>🎫 Battle Pass &amp; Progression</b>

🔹 <code>/pass</code> - View your Battle Pass (Free/Premium/Elite)
🔹 <code>/quests</code> - Daily &amp; Weekly Quests (Earn XP!)
🔹 <code>/referrals</code> - Invite friends &amp; earn rewards
🔹 <code>/achievements</code> - View lifetime milestones &amp; titles
🔹 <code>/level</code> - Check your level progress

<i>💡 Gain XP by catching, battling, and completing quests!</i>
<i>🎁 Unlock rewards at levels 5, 10, 25, and 50</i>
""",
    },
    "OWNER": {
        "text": """
<b>🛠 Admin Tools</b>

🔹 <code>/cnow</code> - [OWNER] Spawn a character immediately
🔹 <code>/ngon</code> - [OWNER] Enable /nguess in a sector
🔹 <code>/ngoff</code> - [OWNER] Disable /nguess in a sector
🔹 <code>/nglist</code> - [OWNER] View authorized sectors
🔹 <code>/broadcast</code> - [OWNER] Send a global message
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
                character = await collection.find_one({'id': char_id})

                if character:
                    response_message = (
                        f"<b>Character Name:</b> {html_escape(character['name'])}\n"
                        f"<b>Anime:</b> {html_escape(character['anime'])}\n"
                        f"<b>Rarity:</b> {html_escape(character['rarity'])}\n"
                        f"<b>Character ID:</b> <code>{character['id']}</code>\n"
                    )

                    await message.reply_photo(
                        photo=character['img_url'],
                        caption=response_message,
                        parse_mode=ParseMode.HTML
                    )
                    return
                else:
                    await message.reply_text("❌ Character not found.", parse_mode=ParseMode.HTML)
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
                            f'🎉 <b>New Referral!</b>\n\n<a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a> joined using your link.\n+500 ⬪ | +50 XP',
                            parse_mode=ParseMode.HTML
                        )
                    except:
                        pass

                    await message.reply_text("🎁 <b>Welcome Bonus!</b>\nYou received <b>1,500 ⬪</b> and a <b>Level 10 Pet</b> for using a referral link! 🚀", parse_mode=ParseMode.HTML)

            except ValueError:
                pass


    if message.chat.type == enums.ChatType.PRIVATE:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [types.InlineKeyboardButton("🌐 Open Web App", web_app=types.WebAppInfo(url=WEB_APP_URL))],
            [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
             types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
            [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
        ])

        first_name = html_escape(message.from_user.first_name)
        text = START_TEXT.format(first_name=first_name, bot_name=BOT_NAME)

        await message.reply_photo(
            photo=random_photo(),
            caption=text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text("✅ <b>I'm active and ready to drop characters!</b>", parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    action = query.data.split(":")[1]

    buttons = [
        [types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    ]
    if query.message.chat.type == enums.ChatType.PRIVATE:
        buttons.append([types.InlineKeyboardButton("🌐 Open Web App", web_app=types.WebAppInfo(url=WEB_APP_URL))])
    else:
        buttons.append([types.InlineKeyboardButton("🌐 Launch Web App (DM)", url=f"https://t.me/{BOT_USERNAME}?start=webapp")])

    buttons.extend([
        [types.InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_CHAT}"),
            types.InlineKeyboardButton("📢 Latest Updates", url=f"https://t.me/{UPDATE_CHAT}")],
        [types.InlineKeyboardButton("❓ Help & Commands", callback_data="help:main")]
    ])
    markup = types.InlineKeyboardMarkup(buttons)

    first_name = html_escape(query.from_user.first_name)
    text = START_TEXT.format(first_name=first_name, bot_name=BOT_NAME)

    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
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
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except errors.MessageNotModified:
        pass

    await query.answer()

def random_photo():
    import random
    return random.choice(PHOTO_URL)

@app.on_message(filters.command("webapp"))
async def webapp_command(_, message):
    web_app_url = config.WEB_APP_URL

    buttons = []
    if message.chat.type == enums.ChatType.PRIVATE:
        buttons.append([types.InlineKeyboardButton("Open Mini App", web_app=types.WebAppInfo(url=web_app_url))])
    else:
        bot_username = getattr(config, "BOT_USERNAME", "Seal_Your_Waifu_Bot")
        buttons.append([types.InlineKeyboardButton("Launch Mini App (DM)", url=f"https://t.me/{bot_username}?start=webapp")])

    keyboard = types.InlineKeyboardMarkup(buttons)

    await message.reply_text(
        "<b>Seal Bot Web Gallery</b>\n\n"
        "Click the button below to view the full character gallery and your collection!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
