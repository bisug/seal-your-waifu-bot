import asyncio
import random
import time
import unicodedata
from datetime import timedelta
from pyrogram import enums, filters, types

from backend import LOGGER, collection, game_bot, sessions_collection
from backend.core.tasks import run_background_task
from backend.core.utils import get_now_utc, html_escape
from backend.modules.gamebot.common import (
    award_gamebot_shards,
    ensure_gamebot_ready,
    ensure_registered_user,
)
# Game settings
TIMEOUT = 60  # 1 minute
SCRAMBLE_SESSION_TTL = timedelta(seconds=TIMEOUT + 30)
REWARD = 250
def normalize_answer(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).casefold()
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in normalized)
    return " ".join(cleaned.split())
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
        # Clean name while preserving non-ASCII letters and numbers.
        clean_name = normalize_answer(original_name)
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
    if not await ensure_gamebot_ready(message):
        return
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
    guess = normalize_answer(message.text)
    target = normalize_answer(session["target_word"])
    if guess == target:
        if not await ensure_registered_user(message.from_user, chat_id):
            return
        # Correct! Attempt to delete session first to prevent double-wins
        res = await sessions_collection.delete_one({"_id": f"scramble:{chat_id}", "start_time": session["start_time"]})
        if res.deleted_count == 0:
            return # Someone else got it or timed out
        user_id = message.from_user.id
        await award_gamebot_shards(
            message.from_user,
            REWARD,
            extra_inc={"scramble_count": 1},
            game_key="scramble",
        )
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
