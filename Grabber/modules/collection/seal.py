from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, OWNER_ID, sudo_users, group_user_totals_collection, LOGGER
from Grabber.core.user import add_char_to_user
from Grabber.core.spawns import get_chat_state, clear_active_spawn, get_message_count, send_character
from Grabber.core.progression import add_xp
from Grabber.modules.progression.quests import update_quest_progress
from Grabber.modules.progression.achievements import check_achievements
import random
import asyncio
from Grabber.modules.collection.rarities import RARITY_WEIGHTS

AUTHORIZED_USERS = set(sudo_users + [OWNER_ID])

@app.on_message(filters.command("seal") & filters.group)
async def seal_handler(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id


    state = await get_chat_state(chat_id)
    character = state.get("last_character")

    if not character:
        return await message.reply_text("❌ There's no character to collect right now!")

    if state.get("first_correct_guess") is not None:
        return

    if len(message.command) < 2:
        return await message.reply_text("❌ Provide the character's name! Usage: <code>/seal &lt;name&gt;</code>", parse_mode=ParseMode.HTML)

    guess = " ".join(message.command[1:]).strip().lower()
    
    # Guess matching logic (REFINED PER USER REQUEST)
    # 1. Normalize both and remove common punctuation
    def normalize(text):
        for char in ".,!?-": text = text.replace(char, " ")
        return " ".join(text.lower().split())

    guess_normalized = normalize(guess)
    correct_normalized = normalize(character['name'])
    
    guess_words = set(guess_normalized.split())
    correct_words = set(correct_normalized.split())

    # RULE 1: Exact Match
    is_match = (guess_normalized == correct_normalized)
    
    # RULE 2: Subset Match (e.g., 'Light' or 'Yagami' catches 'Light Yagami')
    # All words in guess must be one of the words in the correct name.
    if not is_match and guess_words:
        is_match = guess_words.issubset(correct_words)

    if is_match:
        # Atomically try to claim the character
        if not await clear_active_spawn(chat_id, user_id):
            return # Someone else caught it already

        # Enhanced reaction task for v2 compatibility
        async def send_reactions():
            try:
                # Use only foundational reactions
                emojis = ["🔥", "🎉", "🤩", "👏"]
                selected = random.choice(emojis)
                # Some Pyrogram versions require a list, others a single emoji;
                # using the single emoji string is standard for most.
                await app.send_reaction(chat_id, message_id=message.id, emoji=selected)
            except Exception as e:
                LOGGER.debug(f"Reaction task handled: {e}")

        asyncio.create_task(send_reactions())


        await add_char_to_user(user_id, character)


        await group_user_totals_collection.update_one(
            {"group_id": chat_id, "user_id": user_id},
            {"$inc": {"count": 1}},
            upsert=True
        )


        await add_xp(user_id, 10, "character_catch")
        await update_quest_progress(user_id, "catch_master", 1)
        await update_quest_progress(user_id, "weekly_catch", 1)


        await check_achievements(user_id)


        spawn_msg_id = state.get("message_id")
        if spawn_msg_id:
            try:
                await app.delete_messages(chat_id, spawn_msg_id)
            except:
                pass

        caption = (
            f"🎉 <b><a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a> caught the character!</b>\n\n"
            f"📛 <b>Name:</b> {html_escape(character['name'])}\n"
            f"✨ <b>Rarity:</b> {html_escape(character['rarity'])}\n"
            f"🎬 <b>Anime:</b> {html_escape(character['anime'])}\n"
            f"🧤 Added to your harem!"
        )

        await message.reply_photo(character['img_url'], caption=caption, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("❌ Wrong name! Try again.")

@app.on_message(filters.command("messagecount") & filters.group)
async def messagecount_handler(_, message: types.Message):
    count = await get_message_count(message.chat.id)
    await message.reply_text(f"📊 <b>Total messages in this chat:</b> <code>{count}</code>", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("cnow") & filters.group)
async def cnow_handler(_, message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return # Ignore non-owners

    weights_map = RARITY_WEIGHTS
    rarities = list(weights_map.keys())
    weights = list(weights_map.values())
    selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

    await send_character(message.chat.id, selected_rarity)

@app.on_message(filters.command("search"))
async def search_waifu(_, message: types.Message):

    keyboard = [
        [types.InlineKeyboardButton("🔍 Search Waifu", switch_inline_query_current_chat="")]
    ]
    reply_markup = types.InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "🪄 To search for a waifu, click the button below!",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
