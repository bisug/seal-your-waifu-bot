import random
import time
import re
from pyrogram import filters, types
from pyrogram.enums import ParseMode
from Grabber import game_bot, collection, sessions_collection, user_collection, LOGGER, BOT_USERNAME
from Grabber.core.game import update_user_balance
from Grabber.core.utils import html_escape, check_member_requirement

# Game settings
TIMEOUT = 60  # 1 minute
RETRY_LIMIT = 3
REWARD = 100

def scramble_word(word):
    """Shuffles the characters in a word and joins them with hyphens for readability."""
    chars = list(word.upper())
    random.shuffle(chars)
    return "-".join(chars)

async def start_scramble_game(chat_id):
    """Fetches a character and starts a new scramble session."""
    try:
        # Fetch a random character
        cursor = collection.aggregate([{"$sample": {"size": 1}}])
        res = await cursor.to_list(length=1)
        if not res:
            return await game_bot.send_message_safe(chat_id, "❌ <b>Database Error:</b> No characters found.")

        char = res[0]
        # Clean name: remove special chars and pick the first part if it's too long or complex
        # We'll use the full name but simplified
        original_name = char['name']
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', original_name).strip()
        
        # If it's multi-word, we might want to pick one word to make it fun but not impossible
        name_parts = clean_name.split()
        target_word = random.choice(name_parts) if name_parts else clean_name
        
        if len(target_word) < 3: # Too short? use the whole thing
             target_word = "".join(name_parts)

        scrambled = scramble_word(target_word)
        
        # Store session
        await sessions_collection.update_one(
            {"_id": f"scramble:{chat_id}"},
            {"$set": {
                "char": char,
                "target_word": target_word,
                "original_name": original_name,
                "scrambled": scrambled,
                "retries": 0,
                "start_time": time.time()
            }},
            upsert=True
        )

        text = (
            "🧩 <b>Unscramble the Character Name!</b>\n\n"
            f"Series: <b>{html_escape(char['anime'])}</b>\n"
            f"Letters: <code>{scrambled}</code>\n\n"
            f"💰 <b>Reward:</b> {REWARD} Shards\n"
            f"⏱ <b>Time:</b> 1 minute | 🔄 <b>Retries:</b> {RETRY_LIMIT}"
        )

        await game_bot.send_message_safe(chat_id, text, parse_mode=ParseMode.HTML)

    except Exception as e:
        LOGGER.error(f"Error in start_scramble_game: {e}")
        await game_bot.send_message_safe(chat_id, "❌ <b>Error:</b> Could not start the game.")

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
    session = await sessions_collection.find_one({"_id": f"scramble:{chat_id}"})
    
    if not session:
        return

    # Check timeout
    if time.time() - session["start_time"] > TIMEOUT:
        await sessions_collection.delete_one({"_id": f"scramble:{chat_id}"})
        await game_bot.send_message_safe(
            chat_id,
            f"⏱ <b>Time's up!</b>\nThe word was: <b>{html_escape(session['target_word'])}</b> (from {html_escape(session['original_name'])})",
            parse_mode=ParseMode.HTML,
            reply_parameters=types.ReplyParameters(message_id=message.id)
        )
        return

    guess = message.text.lower().strip()
    target = session["target_word"].lower()

    if guess == target:
        # Correct!
        user_id = message.from_user.id
        await update_user_balance(user_id, REWARD)
        await sessions_collection.delete_one({"_id": f"scramble:{chat_id}"})
        
        mention = f'<a href="tg://user?id={user_id}">{html_escape(message.from_user.first_name)}</a>'
        await game_bot.send_message_safe(
            chat_id,
            f"🎉 {mention} unscrambled it correctly!\n"
            f"✅ The word was: <b>{html_escape(session['target_word'])}</b>\n"
            f"💰 <b>Reward:</b> +{REWARD} Shards",
            parse_mode=ParseMode.HTML,
            reply_parameters=types.ReplyParameters(message_id=message.id)
        )
    else:
        # Wrong guess, increment retries
        session = await sessions_collection.find_one_and_update(
            {"_id": f"scramble:{chat_id}"},
            {"$inc": {"retries": 1}},
            return_document=True
        )
        
        if session["retries"] >= RETRY_LIMIT:
            await sessions_collection.delete_one({"_id": f"scramble:{chat_id}"})
            await game_bot.send_message_safe(
                chat_id,
                f"❌ <b>Game Over!</b> Max retries reached.\n"
                f"The word was: <b>{html_escape(session['target_word'])}</b>",
                parse_mode=ParseMode.HTML,
                reply_parameters=types.ReplyParameters(message_id=message.id)
            )
