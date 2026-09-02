import asyncio
import random
import re

from pyrogram import enums, errors, filters, types

from backend.client import app
from backend.core.logging import get_logger
from backend.core.progression import add_xp
from backend.core.rarities import SPAWN_RARITY_WEIGHTS, weighted_pick
from backend.core.roles import sudo_users
from backend.core.spawns import (
    clear_active_spawn,
    get_chat_state,
    get_message_count,
    send_character,
)
from backend.core.tasks import run_background_task
from backend.core.user import add_char_to_user
from backend.core.utils import handle_errors, html_escape, reply_media_dynamic
from backend.database import group_user_totals_collection
from backend.modules.progression.achievements import check_achievements
from backend.modules.progression.quests import update_quest_progress
from config import config

LOGGER = get_logger(__name__)
@app.on_message(filters.command("seal") & filters.group)
@handle_errors
async def seal_handler(_, message: types.Message):
    """Handle core character catching logic for standard spawn messages."""
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    state = await get_chat_state(chat_id)
    character = state.get("last_character")
    if not character:
        return await message.reply_text("There's no character to collect right now!")
    if state.get("first_correct_guess") is not None:
        return
    if len(message.command) < 2:
        return await message.reply_text("Provide the character's name! Usage: <code>/seal &lt;name&gt;</code>", parse_mode=enums.ParseMode.HTML)
    guess = " ".join(message.command[1:]).strip().lower()
    # Guess matching logic
    # 1. Normalize both and remove common punctuation
    def normalize(text):
        return " ".join(re.sub(r'[^\w\s]', ' ', text).lower().split())
    guess_normalized = normalize(guess)
    correct_normalized = normalize(character['name'])
    guess_words = set(guess_normalized.split())
    correct_words = set(correct_normalized.split())
    # RULE 1: Exact Match
    is_match = (guess_normalized == correct_normalized)
    # RULE 2: Subset Match (e.g., 'Light' or 'Yagami' catches 'Light Yagami')
    # All words in guess must be one of the words in the correct name.
    # Guard: every guess word must be >1 char to prevent trivial captures like
    # `/seal d` matching 'Monkey D. Luffy' (d ∈ {monkey, d, luffy} → True).
    if not is_match and guess_words:
        non_trivial = all(len(w) > 1 for w in guess_words)
        is_match = non_trivial and guess_words.issubset(correct_words)
    if is_match:
        # Atomic claim check to prevent race conditions during catch
        if not await clear_active_spawn(chat_id, user_id):
            return # Someone else caught it already
        # Fire the catch reaction in the background
        async def send_reactions():
            try:
                # Use only foundational reactions
                emojis = ["🔥", "🎉", "🤩", "👏"]
                selected = random.choice(emojis)
                # Some Pyrogram versions require a list, others a single emoji;
                # using the single emoji string is standard for most.
                await app.send_reaction(chat_id, message_id=message.id, emoji=selected)
            except errors.MessageIdInvalid:
                pass # Already handled or deleted
            except errors.RPCError as e:
                LOGGER.debug(f"Reaction task handled: {e}")
        run_background_task(send_reactions())
        await add_char_to_user(user_id, character)
        await group_user_totals_collection.update_one(
            {"group_id": chat_id, "user_id": user_id},
            {"$inc": {"count": 1}},
            upsert=True
        )
        # Run independent post-catch operations concurrently (3 sequential DB writes → 1 parallel wait)
        await asyncio.gather(
            add_xp(user_id, 10, "character_catch"),
            update_quest_progress(user_id, "catch_master", 1),
            update_quest_progress(user_id, "weekly_catch", 1),
            update_quest_progress(user_id, "pass_collector", 1),
        )
        # check_achievements reads XP/character state, so it runs after the gather above
        await check_achievements(user_id)
        spawn_msg_id = state.get("message_id")
        if spawn_msg_id:
            try:
                await app.delete_messages(chat_id, spawn_msg_id)
            except errors.RPCError:
                pass
        caption = (
            f"<b><a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a> caught the character!</b>\n\n"
            f"<b>Name:</b> {html_escape(character['name'])}\n"
            f"<b>Rarity:</b> {html_escape(character['rarity'])}\n"
            f"<b>Anime:</b> {html_escape(character['anime'])}\n"
            f"Added to your harem!"
        )
        await reply_media_dynamic(message, character['img_url'], caption=caption, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("messagecount") & filters.group)
@handle_errors
async def messagecount_handler(_, message: types.Message):
    """View the total message count and distance to next spawn."""
    from backend.core.spawn_utils import get_target_spawn_frequency
    chat_id = message.chat.id
    count = await get_message_count(chat_id)
    target_freq, active_count = await get_target_spawn_frequency(chat_id)
    remaining = target_freq - (count % target_freq)
    response = (
        f"📊 <b>Chat Activity Status</b>\n\n"
        f"🔹 <b>Total Messages:</b> <code>{count}</code>\n"
        f"🔹 <b>Active Users:</b> <code>{active_count}</code>\n"
        f"🔹 <b>Spawn Frequency:</b> Every <code>{target_freq}</code> msgs\n"
        f"⏳ <b>Next Spawn In:</b> <code>{remaining}</code> messages"
    )
    await message.reply_text(response, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("cnow") & filters.group)
@handle_errors
async def cnow_handler(_, message: types.Message):
    """Force a character spawn (Owner/Sudo only)."""
    if not message.from_user or (message.from_user.id not in sudo_users and message.from_user.id != config.OWNER_ID):
        return # Ignore non-owners
    selected_rarity = weighted_pick(SPAWN_RARITY_WEIGHTS)
    if selected_rarity:
        await send_character(message.chat.id, selected_rarity, force=True)
@app.on_message(filters.command("search"))
@handle_errors
async def search_waifu(_, message: types.Message):
    keyboard = [
        [types.InlineKeyboardButton("Search Waifu", switch_inline_query_current_chat="")]
    ]
    reply_markup = types.InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "To search for a waifu, click the button below!",
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
