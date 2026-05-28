import asyncio
import random
import re
from pymongo import ReturnDocument
from pyrogram import enums, errors, filters, types
from Grabber import (LOGGER, OWNER_ID, app, collection, game_bot,
                     gamebot_enabled_groups_collection, sessions_collection,
                     user_collection)
from Grabber.core.balance import update_user_balance
from Grabber.core.deletion import schedule_deletion
from Grabber.core.utils import check_member_requirement, html_escape
# Local cache is no longer used for character data to ensure persistence
# Active sessions are stored in sessions_collection with ID: "nguess:{chat_id}"
# Alias for backward compatibility within this file if needed, but better to use it directly
escape_html = html_escape
# Send message safe is now handled by game_bot.send_message_safe and game_bot.send_media_safe
async def start_nguess_game(chat_id):
    """Fetches a character and starts a new game session."""
    # Fetch a random character
    cursor = await collection.aggregate([{"$sample": {"size": 1}}])
    res = await cursor.to_list(length=1)
    if not res:
        return await game_bot.send_message_safe(chat_id, text=html_escape("DATABASE ERROR: No target profiles available."), auto_delete=300)
    char = res[0]
    # Create/Update session in DB
    await sessions_collection.update_one(
        {"_id": f"nguess:{chat_id}"},
        {"$set": {
            "char": char,
            "players": []
        }},
        upsert=True
    )
    anime_name = char['anime']
    briefing = f"Identify this character from the series <b>{html_escape(anime_name)}</b>"
    sent = await game_bot.send_media_safe(
        chat_id,
        media_url=char['img_url'],
        caption=briefing,
        auto_delete=300
    )
    if not sent:
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}"})
        await game_bot.send_message_safe(chat_id, text=html_escape("CRITICAL FAILURE: Transponder link lost."), auto_delete=300)
def get_name_variants(name: str):
    """Generates possible name variants for matching."""
    name = name.lower().strip()
    parts = re.split(r'\s+', name)
    variants = {name}
    for part in parts:
        if len(part) > 2:
            variants.add(part)
    return variants
@game_bot.on_message(filters.command("nguess"))
async def nguess_start_handler(_, message: types.Message):
    chat_id = message.chat.id
    meets_req, reason, count = await check_member_requirement(game_bot, message.chat)
    if not meets_req:
        if reason == "group_only":
            text = "❌ <b>Group Required:</b> This game can only be played in group chats."
        elif reason == "member_count":
            text = (
                f"⚠️ <b>Security Level Low:</b> This sector must contain at least <b>50 personnel</b> (members) to authorize GameBot operations.\n\n"
                f"Current count: <code>{count}</code>"
            )
        else: # main_bot_missing
            from Grabber import BOT_NAME, BOT_USERNAME
            text = (
                f"🚫 <b>Main Bot Missing:</b> GameBot operations require the presence of <b>{BOT_NAME}</b> (@{BOT_USERNAME}) in this sector.\n\n"
                f"<i>Please add the Main Bot to authorize games!</i>"
            )
        return await game_bot.send_message_safe(chat_id, text, auto_delete=300)
    # If a game is active, we just proceed to start a new one (per user request: "send next instead")
    await start_nguess_game(chat_id)
@game_bot.on_message(filters.text & filters.group & ~filters.command(["nguess", "top", "ctop"]), group=10)
async def nguess_check_handler(_, message: types.Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    # Update player list atomically
    session = await sessions_collection.find_one_and_update(
        {"_id": f"nguess:{chat_id}"},
        {"$addToSet": {"players": message.from_user.id}},
        return_document=ReturnDocument.AFTER
    )
    if not session:
        return
    guess = message.text.lower().strip()
    char = session["char"]
    name_variants = get_name_variants(char['name'])
    if guess in name_variants:
        # Check registration before rewarding
        from Grabber.core.user import get_cached_user
        cached = await get_cached_user(message.from_user.id)
        if not cached:
            db_user = await user_collection.find_one({"id": {"$in": [message.from_user.id, str(message.from_user.id)]}})
            if not db_user:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from config import config
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Start Bot in DM", url=f"https://t.me/{config.BOT_USERNAME}?start=true")
                ]])
                text = f"❌ <b>Guess Ignored!</b>\n\n<a href='tg://user?id={message.from_user.id}'>{html_escape(message.from_user.first_name)}</a>, you must start the bot in private messages first to play and earn shards!"
                return await game_bot.send_message_safe(chat_id, text=text, reply_markup=markup, auto_delete=30)
                
        # Correct guess!
        player_count = len(session.get("players", []))
        reward = min(10 + (player_count - 1) * 5, 50)
        # Increment global counter
        stats = await sessions_collection.find_one_and_update(
            {"id": "nguess_global_stats"},
            {"$inc": {"total_guesses": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        total_guesses = stats.get("total_guesses", 1)
        bonus = 0
        milestone_text = ""
        if total_guesses % 100 == 0:
            bonus = 1000
            milestone_text = f"\n\n<b>ELITE MILESTONE ACHIEVED</b>\nYou are the 100th guesser! Granted 1,000 bonus Shards."
            await sessions_collection.update_one({"id": "nguess_global_stats"}, {"$set": {"total_guesses": 0}})
        elif total_guesses % 100 == 50:
            bonus = 500
            milestone_text = f"\n\n<b>MILESTONE REACHED</b>\nYou are the 50th guesser! Granted 500 bonus Shards."
        total_reward = reward + bonus
        # Update user
        await user_collection.update_one(
            {"id": message.from_user.id},
            {
                "$inc": {"balance": total_reward, "guess_count": 1},
                "$setOnInsert": {"first_name": message.from_user.first_name}
            },
            upsert=True
        )

        # Track Quests and Achievements
        from Grabber.modules.progression.quests import update_quest_progress
        from Grabber.modules.progression.achievements import check_achievements
        asyncio.create_task(update_quest_progress(message.from_user.id, "guesser", 1))
        asyncio.create_task(update_quest_progress(message.from_user.id, "weekly_guesser", 1))
        asyncio.create_task(check_achievements(message.from_user.id))

        # Delete session
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}"})
        display_progress = total_guesses % 100 if total_guesses % 100 != 0 else 100
        mention = f'<a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>'
        target_name = html_escape(char['name'])
        success_msg = (
            f"✅ {mention} identified <b>{target_name}</b>!\n"
            f"💰 <b>Bounty:</b> +{reward} Shards\n"
            f"🔥 <b>Progress:</b> {display_progress}/100{milestone_text}"
        )
        await game_bot.send_message_safe(chat_id, text=success_msg, auto_delete=300)
        # Recursive start
        await start_nguess_game(chat_id)
    else:
        # Silently ignore wrong guesses
        pass
