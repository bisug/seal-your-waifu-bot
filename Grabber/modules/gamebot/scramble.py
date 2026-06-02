import asyncio
import random
import re
import time
from datetime import timedelta
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import (LOGGER, collection, game_bot, sessions_collection,
                     user_collection)
from Grabber.core.balance import update_user_balance
from Grabber.core.tasks import run_background_task
from Grabber.core.utils import check_member_requirement, get_now_utc, html_escape
# Game settings
TIMEOUT = 60  # 1 minute
SCRAMBLE_SESSION_TTL = timedelta(seconds=TIMEOUT + 30)
REWARD = 100
def scramble_word(word):
    """Shuffles the characters in a word and joins them with hyphens for readability.
    Ensures the scrambled word is not the same as the original.
    """
    word_upper = word.upper()
    chars = list(word_upper)
    if len(chars) <= 1:
        return "-".join(chars)
    scrambled = "".join(chars)
    attempts = 0
    while scrambled == word_upper and attempts < 10:
        random.shuffle(chars)
        scrambled = "".join(chars)
        attempts += 1
    return "-".join(chars)
async def game_timeout_manager(chat_id, start_time):
    """Wait for TIMEOUT and then check if the game is still active."""
    await asyncio.sleep(TIMEOUT)
    session = await sessions_collection.find_one({"_id": f"scramble:{chat_id}"})
    if session and session.get("start_time") == start_time:
        # Game still active and it's the SAME session (not a new one)
        await sessions_collection.delete_one({"_id": f"scramble:{chat_id}"})
        target = session.get("target_word", "Unknown")
        char_name = session.get("original_name", "Unknown")
        text = (
            f"⏱ <b>Time's up!</b>\n"
            f"The word was: <b>{html_escape(target)}</b>\n"
            f"Character: <b>{html_escape(char_name)}</b>"
        )
        await game_bot.send_message_safe(chat_id, text)
async def start_scramble_game(chat_id):
    """Fetches a character and starts a new scramble session."""
    try:
        # Anti-spam: Check for active session
        existing = await sessions_collection.find_one({"_id": f"scramble:{chat_id}"})
        if existing:
            elapsed = time.time() - existing.get("start_time", 0)
            if elapsed < TIMEOUT:
                return await game_bot.send_message_safe(
                    chat_id, 
                    f"⚠️ <b>Game Active:</b> A scramble game is already in progress! Use <code>/scramble</code> again in {int(TIMEOUT - elapsed)}s if no one identifies it.",
                    auto_delete=30
                )
        # Fetch a random character
        cursor = await collection.aggregate([{"$sample": {"size": 1}}])
        res = await cursor.to_list(length=1)
        if not res:
            return await game_bot.send_message_safe(chat_id, "❌ <b>Database Error:</b> No characters found.")
        char = res[0]
        original_name = char['name']
        # Clean name: remove special chars
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', original_name).strip()
        name_parts = clean_name.split()
        # Selection logic: pick a word with length >= 4 if possible
        candidates = [p for p in name_parts if len(p) >= 4]
        if not candidates:
             candidates = name_parts if name_parts else [clean_name]
        target_word = random.choice(candidates)
        scrambled = scramble_word(target_word)
        start_time = time.time()
        # Store session
        await sessions_collection.update_one(
            {"_id": f"scramble:{chat_id}"},
            {"$set": {
                "char": char,
                "target_word": target_word,
                "original_name": original_name,
                "scrambled": scrambled,
                "start_time": start_time,
                "expires_at_dt": get_now_utc() + SCRAMBLE_SESSION_TTL,
            }},
            upsert=True
        )
        text = (
            "🧩 <b>Unscramble the Character Name!</b>\n\n"
            f"Series: <b>{html_escape(char['anime'])}</b>\n"
            f"Letters: <code>{scrambled}</code>\n\n"
            f"💰 <b>Reward:</b> {REWARD} Shards\n"
            f"⏱ <b>Time:</b> 1 minute"
        )
        await game_bot.send_message_safe(chat_id, text, parse_mode=enums.ParseMode.HTML)
        # Active timeout monitor
        run_background_task(game_timeout_manager(chat_id, start_time))
    except Exception as e:
        LOGGER.error(f"Error in start_scramble_game: {e}")
        await game_bot.send_message_safe(chat_id, "❌ <b>Error:</b> Could not authorize the game transponder.")
@game_bot.on_message(filters.command("scramble"))
async def scramble_cmd_handler(_, message: types.Message):
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
        return await game_bot.send_message_safe(message.chat.id, text, auto_delete=300)
    await start_scramble_game(message.chat.id)
@game_bot.on_message(filters.text & filters.group, group=11)
async def scramble_guess_handler(_, message: types.Message):
    if not message.text or message.text.startswith("/") or not message.from_user:
        return
    chat_id = message.chat.id
    # Quick check for session without heavy DB load if possible, but we need the session data
    now = get_now_utc()
    session = await sessions_collection.find_one({
        "_id": f"scramble:{chat_id}",
        "$or": [
            {"expires_at_dt": {"$exists": False}},
            {"expires_at_dt": {"$gt": now}},
        ],
    })
    if not session:
        return
    # Check timeout (secondary protection)
    if time.time() - session["start_time"] > TIMEOUT + 5: # 5s buffer for the worker
        # Let the worker handle it or clean up if it missed
        return
    guess = message.text.lower().strip()
    target = session["target_word"].lower()
    if guess == target:
        # Correct! Attempt to delete session first to prevent double-wins
        res = await sessions_collection.delete_one({"_id": f"scramble:{chat_id}", "start_time": session["start_time"]})
        if res.deleted_count == 0:
            return # Someone else got it or timed out
        user_id = message.from_user.id
        await update_user_balance(user_id, REWARD)
        mention = f'<a href="tg://user?id={user_id}">{html_escape(message.from_user.first_name)}</a>'
        await game_bot.send_message_safe(
            chat_id,
            f"🎉 {mention} unscrambled it correctly!\n"
            f"✅ The word was: <b>{html_escape(session['target_word'])}</b>\n"
            f"👤 Character: <b>{html_escape(session['original_name'])}</b>\n"
            f"💰 <b>Reward:</b> +{REWARD} Shards",
            parse_mode=enums.ParseMode.HTML,
            reply_parameters=types.ReplyParameters(message_id=message.id)
        )
