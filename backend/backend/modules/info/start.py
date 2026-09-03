import random
import uuid
from datetime import datetime, timezone

from pyrogram import enums, errors, filters, types

from backend.client import app
from backend.core.cache import invalidate_user_cache
from backend.core.eggs import roll_egg_tier
from backend.core.keyboard import KeyboardBuilder, get_webapp_button
from backend.core.leaderboard import (
    get_total_ranked_users,
    get_user_rank,
    update_user_rank,
)
from backend.core.logging import get_logger
from backend.core.progression import get_user_progress
from backend.core.rarities import CLAIM_RARITY_WEIGHTS, weighted_pick
from backend.core.referrals import claim_referral_bonus, parse_referral_payload
from backend.core.user import add_user_set_on_insert, ensure_user_document, get_user_filter
from backend.core.utils import handle_errors, html_escape, reply_media_dynamic
from backend.core.waifu import sample_character_by_rarity
from backend.database import collection, total_pm_users, user_collection
from config import config

LOGGER = get_logger(__name__)
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
/reedem <code> - Redeem waifugen codes
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
/exchange - Currency exchange
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
/profile - Collector profile
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
/gban - [SUDO] Globally ban a user for 30 days
/ungban - [SUDO] Remove a global user ban
/gbangroup - [SUDO] Globally ban a group for 30 days
/ungbangroup - [SUDO] Remove a global group ban
/gbanlist - [SUDO] List global bans
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
        types.InlineKeyboardButton("Support", url=f"https://t.me/{config.SUPPORT_CHAT}"),
        types.InlineKeyboardButton("Updates", url=f"https://t.me/{config.UPDATE_CHAT}")
    )
    if is_private and (not existing_user or not existing_user.get("free_spin_claimed")):
        builder.add_row(
            types.InlineKeyboardButton("🎁 Free Spin (New Player!)", callback_data="free_spin")
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
async def _handle_locate_param(message: types.Message, param: str) -> bool:
    """Deep link locate_{id}: show the character card. Returns True if handled."""
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
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text("❌ Character not found.", parse_mode=enums.ParseMode.HTML)
        return True
    except Exception as e:
        LOGGER.error(f"Locate Error: {e}")
        return False


async def _handle_claim_param(message: types.Message, param: str) -> bool:
    """Deep link claim_{code}: redeem a giveaway character. Returns True if handled."""
    try:
        code = param.split("_")[1]
        from backend.modules.admin.giveaway import process_core_claim
        success, result = await process_core_claim(app, message.from_user, code)
        if not success:
            await message.reply_text(result, parse_mode=enums.ParseMode.HTML)
        else:
            waifu = result
            response_text = (
                f'🎉 Congratulations <a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>!\n'
                f"You claimed a <b>{html_escape(waifu['rarity'])}</b> character!\n\n"
                f"Name: {html_escape(waifu['name'])}\n"
                f"Anime: {html_escape(waifu['anime'])}\n"
                f"ID: <code>{waifu['id']}</code>\n"
            )
            await reply_media_dynamic(message, waifu['img_url'], caption=response_text, parse_mode=enums.ParseMode.HTML)
        return True
    except Exception as e:
        LOGGER.error(f"Claim Error: {e}")
        return False


async def _handle_referral_param(message: types.Message, param: str, *, is_new_user: bool) -> bool:
    """Deep link ref_{id}: apply referral bonus and notify both sides. True if handled."""
    user_id = message.from_user.id
    first_name_clean = message.from_user.first_name
    referral_result = await claim_referral_bonus(
        user_id=user_id,
        referrer_id=parse_referral_payload(param),
        is_new_user=is_new_user,
        first_name=first_name_clean,
        username=message.from_user.username,
    )
    if referral_result.applied:
        try:
            await app.send_message(
                referral_result.referrer_id,
                (
                    f'🎉 <b>New Referral!</b>\n\n'
                    f'<a href="tg://user?id={message.from_user.id}">{html_escape(first_name_clean)}</a> '
                    f"joined using your link.\n"
                    f"+{referral_result.referrer_reward_shards:,} ⬪ | "
                    f"+{referral_result.referrer_reward_xp:,} XP"
                ),
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
        await message.reply_text(
            (
                "🎁 <b>Welcome Bonus!</b>\n"
                f"You received <b>{referral_result.referred_reward_shards:,} ⬪</b> "
                f"and a <b>Level {referral_result.referred_pet_level} Pet</b> "
                "for using a referral link! 🚀"
            ),
            parse_mode=enums.ParseMode.HTML,
        )
    return True


async def _handle_bonus_param(message: types.Message) -> bool:
    """Deep link bonus_: daily bonus roll in the bot's DM.

    Random reward: an egg, a character (claim-weighted rarities), or a small
    shard pile. Once per UTC day, guarded atomically so double-taps and
    concurrent /daily claims can't both pay out.
    """
    user_id = message.from_user.id
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Atomic claim: only the first writer of today's date wins.
    claim_filter = get_user_filter(user_id)
    claim_filter["last_bonus_date"] = {"$ne": now_date}
    roll = random.random()
    update_op: dict = {"$set": {"last_bonus_date": now_date}}
    reward_kind = "coins"
    if roll < 0.35:
        # Egg: full-luck tier roll (same distribution as hunts).
        from backend.core.constants import EGG_TIERS
        tier_key = roll_egg_tier(0.0, 0.0)
        tier_data = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
        egg = {
            "id": f"egg_{uuid.uuid4().hex[:12]}",
            "tier": tier_key,
            "name": tier_data["name"],
            "obtained_at": datetime.now(timezone.utc),
            "status": "fresh",
            "is_corrupted": False,
        }
        update_op["$push"] = {"eggs": egg}
        reward_kind = "egg"
        reward_label = tier_data["name"]
    elif roll < 0.80:
        # Character: claim-weighted rarity, same pool as /daily waifu.
        rarity = weighted_pick(CLAIM_RARITY_WEIGHTS)
        char = await sample_character_by_rarity(rarity) if rarity else None
        if char:
            update_op["$push"] = {"characters": char}
            update_op["$inc"] = {"char_count": 1, "version": 1}
            reward_kind = "character"
            reward_label = f"{char['rarity']} — {char['name']}"
        else:
            update_op["$inc"] = {"balance": 500, "version": 1}
            reward_label = "500 ⬪"
    else:
        coins = random.randint(300, 800)
        update_op["$inc"] = {"balance": coins, "version": 1}
        reward_label = f"{coins:,} ⬪"

    try:
        result = await user_collection.update_one(
            claim_filter,
            add_user_set_on_insert(update_op, user_id),
            upsert=True,
        )
    except Exception:
        # Fail-safe: never break /start over a bonus. The atomic date guard
        # makes a retry safe, so tell the user to tap again.
        LOGGER.exception("Bonus claim DB error for %s", user_id)
        await message.reply_text(
            "🎁 <b>Bonus hiccup!</b> Please tap the button again in a minute.",
            parse_mode=enums.ParseMode.HTML,
        )
        return True
    if result.modified_count == 0 and result.upserted_id is None:
        await message.reply_text(
            "🎁 <b>Bonus already claimed today!</b>\nCome back tomorrow, Collector.",
            parse_mode=enums.ParseMode.HTML,
        )
        return True
    await invalidate_user_cache(user_id)

    if reward_kind == "character":
        await reply_media_dynamic(
            message,
            char["img_url"],
            caption=(
                "🎁 <b>Daily Bonus!</b>\n\n"
                f"You found <b>{html_escape(char['name'])}</b>\n"
                f"<b>{html_escape(char['rarity'])}</b> • {html_escape(char['anime'])}\n\n"
                "<i>Come back tomorrow for more!</i>"
            ),
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await message.reply_text(
            f"🎁 <b>Daily Bonus!</b>\n\nYou received: <b>{html_escape(str(reward_label))}</b>\n\n"
            "<i>Come back tomorrow for more!</i>",
            parse_mode=enums.ParseMode.HTML,
        )
    return True


async def _handle_deep_link(message: types.Message, param: str, *, is_new_user: bool) -> bool:
    """Dispatch a /start deep-link payload. Returns True when the payload was consumed."""
    if param.startswith("locate_"):
        return await _handle_locate_param(message, param)
    if param.startswith("claim_"):
        return await _handle_claim_param(message, param)
    if param.startswith("ref_"):
        return await _handle_referral_param(message, param, is_new_user=is_new_user)
    if param.startswith("bonus"):
        return await _handle_bonus_param(message)
    return False


@app.on_message(filters.command("start"))
@handle_errors
async def start_handler(_, message: types.Message):
    """Entry point for the bot. Handles new users and referral links."""
    user_id = message.from_user.id
    first_name_clean = message.from_user.first_name
    existing_user = await user_collection.find_one(get_user_filter(user_id))
    is_new_user = existing_user is None
    await ensure_user_document(
        user_id,
        first_name=first_name_clean,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
    )
    # Broadcast list only needs the id; names live on the user document.
    await total_pm_users.update_one(
        {"_id": user_id},
        {"$setOnInsert": {"_id": user_id}},
        upsert=True
    )
    if len(message.command) > 1:
        await _handle_deep_link(message, message.command[1], is_new_user=is_new_user)
    is_private = message.chat.type == enums.ChatType.PRIVATE
    # Refresh user state after referral DB logic just in case
    if is_new_user:
        existing_user = await user_collection.find_one(get_user_filter(user_id))
    text, markup = await render_start_message(user_id, first_name_clean, is_private, existing_user)
    if is_private:
        await reply_media_dynamic(message, random_photo(),
            caption=text,
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("help"))
@handle_errors
async def help_command(_, message: types.Message):
    data = HELP_DATA["MAIN"]
    await message.reply_text(
        data["text"],
        reply_markup=types.InlineKeyboardMarkup(data["buttons"]),
        parse_mode=enums.ParseMode.HTML,
    )


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
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
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
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass

@app.on_callback_query(filters.regex(r"^free_spin$"))
@handle_errors
async def free_spin_handler(_, query: types.CallbackQuery):
    """Handle the one-time free spin for new users."""
    user_id = query.from_user.id
    existing_user = await user_collection.find_one(get_user_filter(user_id))
    
    if existing_user and existing_user.get("free_spin_claimed"):
        await query.answer("You have already used your free spin!", show_alert=True)
        return
        
    cursor = await collection.aggregate([{"$sample": {"size": 1}}])
    chars = await cursor.to_list(length=1)
    
    if not chars:
        await query.answer("No characters available in the bot yet.", show_alert=True)
        return
        
    waifu = chars[0]
    waifu_data = waifu.copy()
    waifu_data.pop('_id', None)
    
    claim_filter = get_user_filter(user_id)
    claim_filter["free_spin_claimed"] = {"$ne": True}
    claim_result = await user_collection.update_one(
        claim_filter,
        add_user_set_on_insert(
            {
                "$set": {"free_spin_claimed": True},
                "$push": {"characters": waifu_data},
                "$inc": {"char_count": 1, "version": 1},
            },
            user_id,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name,
            username=query.from_user.username,
        ),
        upsert=True,
    )
    if claim_result.modified_count == 0 and claim_result.upserted_id is None:
        await query.answer("You have already used your free spin!", show_alert=True)
        return

    user_after_claim = await user_collection.find_one(get_user_filter(user_id), {"char_count": 1})
    await update_user_rank(user_id, user_after_claim.get("char_count", 1) if user_after_claim else 1, metric="harem")
    await invalidate_user_cache(user_id)
    
    response_text = (
        f'🎉 Congratulations <a href="tg://user?id={user_id}">{html_escape(query.from_user.first_name)}</a>!\n'
        f"You used your Free Spin and got a <b>{html_escape(waifu_data['rarity'])}</b> character!\n\n"
        f"<b>Name:</b> {html_escape(waifu_data['name'])}\n"
        f"<b>Anime:</b> {html_escape(waifu_data['anime'])}\n"
        f"<b>ID:</b> <code>{waifu_data['id']}</code>\n"
    )
    
    await query.message.reply_photo(
        photo=waifu_data['img_url'],
        caption=response_text,
        parse_mode=enums.ParseMode.HTML
    )
    
    # Reload start menu to remove the spin button
    existing_user = await user_collection.find_one(get_user_filter(user_id))
    text, markup = await render_start_message(user_id, query.from_user.first_name, True, existing_user)
    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass

def random_photo():
    return random.choice(config.PHOTO_URL)
@app.on_message(filters.command("webapp"))
@handle_errors
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
        parse_mode=enums.ParseMode.HTML
    )
