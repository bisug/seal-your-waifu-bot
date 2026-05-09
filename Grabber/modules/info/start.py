from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import (LOGGER, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, WEB_APP_URL,
                     app, collection, total_pm_users, user_collection)
from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
from Grabber.core.progression import add_xp, get_user_progress
from Grabber.core.user import get_user_filter, get_user_id, update_user
from Grabber.core.cache import get_user_rank, get_total_ranked_users
from Grabber.core.utils import html_escape, reply_media_dynamic
from Grabber.modules.progression.achievements import check_achievements
from Grabber.modules.progression.pet import DEFAULT_PET

LOGGER.info("Loading Start module...")

START_TEXT_NEW = """
<b>{bot_name}</b>

<blockquote>“In the world of anime, some seek power, others seek glory. But a true <b>Collector</b> seeks them all.”</blockquote>

<b>Greetings, Collector {first_name}!</b>
I am your ultimate companion for character collecting and strategic duels.

<b>Catch</b> • <b>Duel</b> • <b>Hatch</b> • <b>Collect</b>

<i>Add me to a group to begin your journey!</i>
"""

START_TEXT_RETURNING = """
<b>{bot_name} Dashboard</b>

<b>Welcome back, {first_name}!</b>
━━━━━━━━━━━━━━━━━━━━━
<b>Rank:</b> <code>#{rank}</code> / {total_ranked}
<b>Level:</b> <code>{level}</code>
<b>Balance:</b> <code>{balance}</code> ⬪ | <code>{zenith}</code> ⧫
<b>Harem:</b> <code>{harem_size}</code> Unique Characters
━━━━━━━━━━━━━━━━━━━━━
<i>Select an option below to continue your journey!</i>
"""

HELP_DATA = {
    "MAIN": {
        "text": "<b>Seal Bot - Help Menu</b>\n\nSelect a category below to see available commands:",
        "buttons": [
            [types.InlineKeyboardButton("Core Basics", callback_data="help:core", style=enums.ButtonStyle.PRIMARY),
             types.InlineKeyboardButton("Pet System", callback_data="help:pet", style=enums.ButtonStyle.PRIMARY)],
            [types.InlineKeyboardButton("Battle & Economy", callback_data="help:battle", style=enums.ButtonStyle.PRIMARY),
             types.InlineKeyboardButton("Progression", callback_data="help:progression", style=enums.ButtonStyle.PRIMARY)],
            [types.InlineKeyboardButton("Info & Stats", callback_data="help:info", style=enums.ButtonStyle.PRIMARY),
             types.InlineKeyboardButton("Admin Tools", callback_data="help:owner", style=enums.ButtonStyle.DANGER)],
            [types.InlineKeyboardButton("Back to Dashboard", callback_data="st:b")]
        ]
    },
    "CORE": {
        "text": """
<b>Core Commands</b>

/start - Start the bot
/help - Show help menu
/search - Find a waifu
/harem - Your collection
/fav - Set favorite character
/trade - Trade characters
/gift - Gift characters
/transfer - Full collection merge
/claim - Claim waifu codes
""",
    },
    "PET": {
        "text": """
<b>Pet System</b>

/petshop - Buy powerful pets
/mypet - Manage your pet
/hunt - Send pet to hunt
/eggs - View your eggs
/hatch - Hatch char eggs
/feed - Feed your pet
/train - Train your pet
""",
    },
    "BATTLE": {
        "text": """
<b>Battle & Economy</b>

/battle - Start a PvP duel
/balance - Check your balance
/zenith - Shards to Zenith
/shard - Zenith to Shards
/shop - Open the shop
/daily - Claim daily rewards
/weekly - Claim weekly bonus
/top - Global leaderboard
/bet - Gamble Shards
/pay - Send Shards to user
/sell - Sell a character
""",
    },
    "INFO": {
        "text": """
<b>Info & Stats</b>

/stats - Bot statistics
/rarities - Character counts
/ctop - Chat leaderboard
/mtop - Rich leaderboard
/ping - Check bot status
/webapp - Open Mini-App
/check - User status check
/animes - Available anime list
/sani - Search by anime
""",
    },
    "PROGRESSION": {
        "text": """
<b>Battle Pass & Progress</b>

/pass - View Battle Pass
/quests - Active quests
/referrals - Invite friends
/achievements - Milestones
/level - Your level progress
/propose - Propose to a user
/seal - Use a seal item

<i>Catch characters and battle to level up!</i>
""",
    },
    "OWNER": {
        "text": """
<b>Admin Tools</b>

/cnow - [OWNER] Spawn a character immediately
/broadcast - [OWNER] Send a global message
""",
    }
}

async def render_start_message(user_id: int, first_name: str, is_private: bool, existing_user: dict = None):
    """Helper method to dynamically build the Smart Dashboard for the start menu."""
    builder = KeyboardBuilder()
    builder.add_button("Add to Group", url=f"https://t.me/{config.BOT_USERNAME}?startgroup=true")
    
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        builder.add_row(webapp_btn)

    builder.add_row(
        types.InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}"),
        types.InlineKeyboardButton("Updates", url=f"https://t.me/{UPDATE_CHAT}")
    )
    builder.add_row(
        types.InlineKeyboardButton("My Collection", callback_data="harem_view:self"),
        types.InlineKeyboardButton("Help Menu", callback_data="help:main", style=enums.ButtonStyle.PRIMARY)
    )
    markup = builder.build()

    if not is_private:
        return "✅ <b>I'm active and ready to drop characters!</b>", markup

    if existing_user and existing_user.get("characters"):
        progress = await get_user_progress(user_id, user_data=existing_user)
        rank = await get_user_rank(user_id) or "N/A"
        total_ranked = await get_total_ranked_users() or "???"
        
        balance = existing_user.get("balance", 0)
        zenith = existing_user.get("zenith", 0)
        
        unique_chars = {c.get("id") for c in existing_user.get("characters", [])}
        harem_size = len(unique_chars)
        
        text = START_TEXT_RETURNING.format(
            bot_name=config.BOT_NAME,
            first_name=html_escape(first_name),
            rank=rank,
            total_ranked=total_ranked,
            level=progress['level'],
            balance=f"{balance:,}",
            zenith=f"{zenith:,}",
            harem_size=f"{harem_size:,}"
        )
    else:
        text = START_TEXT_NEW.format(
            first_name=html_escape(first_name), 
            bot_name=config.BOT_NAME
        )
        
    return text, markup


@app.on_message(filters.command("start"))
async def start_handler(_, message: types.Message):
    """Entry point for the bot. Handles new users and referral links."""
    user_id = message.from_user.id
    first_name_clean = message.from_user.first_name
    
    existing_user = await user_collection.find_one(get_user_filter(user_id))

    await total_pm_users.update_one(
        {"_id": user_id},
        {"$set": {"first_name": first_name_clean, "username": message.from_user.username}},
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
                    await reply_media_dynamic(message, character['img_url'],
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
        elif param.startswith("claim_"):
            try:
                code = param.split("_")[1]
                from Grabber.modules.admin.giveaway import process_core_claim
                success, result = await process_core_claim(app, message.from_user, code)
                
                if not success:
                    await message.reply_text(result, parse_mode=ParseMode.HTML)
                else:
                    waifu = result
                    response_text = (
                        f'🎉 Congratulations <a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>!\n'
                        f"You claimed a <b>{html_escape(waifu['rarity'])}</b> character!\n\n"
                        f"Name: {html_escape(waifu['name'])}\n"
                        f"Anime: {html_escape(waifu['anime'])}\n"
                        f"ID: <code>{waifu['id']}</code>\n"
                    )
                    await reply_media_dynamic(message, waifu['img_url'], caption=response_text, parse_mode=ParseMode.HTML)
                return
            except Exception as e:
                LOGGER.error(f"Claim Error: {e}")
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
                        {"id": get_user_id(user_id)},
                        {"$set": {"pets": [upgraded_pet], "current_pet": upgraded_pet["name"], "referred_by": referrer_id}},
                        upsert=True
                    )
                    await update_user(user_id, {"$inc": {"balance": 1500}})
                    
                    await update_user(referrer_id, {"$inc": {"balance": 500, "referrals_count": 1, "referrals_earned": 500}})
                    await add_xp(referrer_id, 50, "referral")
                    await check_achievements(referrer_id)
                    try:
                        await app.send_message(
                            referrer_id,
                            f'🎉 <b>New Referral!</b>\n\n<a href="tg://user?id={message.from_user.id}">{html_escape(first_name_clean)}</a> joined using your link.\n+500 ⬪ | +50 XP',
                            parse_mode=ParseMode.HTML
                        )
                    except:
                        pass
                    await message.reply_text("🎁 <b>Welcome Bonus!</b>\nYou received <b>1,500 ⬪</b> and a <b>Level 10 Pet</b> for using a referral link! 🚀", parse_mode=ParseMode.HTML)
            except ValueError:
                pass

    is_private = message.chat.type == enums.ChatType.PRIVATE
    
    # Refresh user state after referral DB logic just in case
    if not existing_user:
        existing_user = await user_collection.find_one(get_user_filter(user_id))
        
    text, markup = await render_start_message(user_id, first_name_clean, is_private, existing_user)

    if is_private:
        await reply_media_dynamic(message, random_photo(),
            caption=text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(text, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^st:(h|b)"))
async def start_callback_handler(_, query: types.CallbackQuery):
    """Handle navigation back to the start menu from help or collection pages."""
    await query.answer()
    is_private = query.message.chat.type == enums.ChatType.PRIVATE
    user_id = query.from_user.id
    
    existing_user = await user_collection.find_one(get_user_filter(user_id))
    text, markup = await render_start_message(user_id, query.from_user.first_name, is_private, existing_user)

    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except errors.MessageNotModified:
        pass

@app.on_callback_query(filters.regex(r"^help:(.+)"))
async def help_callback_handler(_, query: types.CallbackQuery):
    """Handle navigation within the multi-category help menu."""
    await query.answer()
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

def random_photo():
    import random
    return random.choice(PHOTO_URL)

@app.on_message(filters.command("webapp"))
async def webapp_command(_, message):
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private)
    builder = KeyboardBuilder()
    builder.add_row(webapp_btn)
    keyboard = builder.build()

    await message.reply_text(
        "<b>Seal Bot Web Gallery</b>\n\n"
        "Click the button below to view the full character gallery and your collection!",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
