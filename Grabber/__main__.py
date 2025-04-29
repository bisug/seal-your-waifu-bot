import importlib
import time
import random
import asyncio
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from Grabber import (
    collection, db, user_collection, message_counts_collection,
    application, LOGGER, user_totals_collection, Grabberu
)
from Grabber.modules import ALL_MODULES

# --- Constants ---
SPECIAL_GROUP_ID = -1002528887253  # Royal spawns only here
ROYAL_NOTIFY_USER_ID = 7717913705  # Send royal info to this user

# --- Globals ---
locks = {}
message_counts = {}
waifu_spawn_order = {}
last_characters = {}
first_correct_guesses = {}
waifu_message = {}
warned_users = {}

# --- Rarity ---
rarity_map = {
    1: "⚪ Common", 2: "🟢 Medium", 3: "🟠 Rare", 4: "🟡 Legendary",
    5: "💠 Cosmic", 6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🫧 Royal"
}

rarity_spawn_order = ["⚪ Common", "🟢 Medium", "🟠 Rare", "🟡 Legendary"]

special_rarity_thresholds = {
    "💠 Cosmic": 300,
    "💮 Exclusive": 600,
    "🔮 Limited Edition": 900,
    "🫧 Royal": 1000
}

# --- Module Loader ---
for module_name in ALL_MODULES:
    importlib.import_module("Grabber.modules." + module_name)


# --- Message Counter ---
async def load_message_counts():
    global message_counts
    cursor = message_counts_collection.find({})
    async for doc in cursor:
        message_counts[str(doc["chat_id"])] = doc["count"]

async def save_message_counts():
    for chat_id, count in message_counts.items():
        await message_counts_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"count": count}},
            upsert=True
        )

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if not user:
        return

    user_id = user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        if chat_id not in message_counts:
            data = await message_counts_collection.find_one({"chat_id": chat_id})
            message_counts[chat_id] = data["count"] if data else 0

        chat_settings = await user_totals_collection.find_one({"chat_id": chat_id})
        message_frequency = chat_settings.get("message_frequency", 100) if chat_settings else 100

        message_counts[chat_id] += 1

        for rarity, threshold in special_rarity_thresholds.items():
            if message_counts[chat_id] % threshold == 0:
                if rarity == "🫧 Royal" and int(chat_id) != SPECIAL_GROUP_ID:
                    continue
                await send_character(update, context, rarity)
                return

        if message_counts[chat_id] % message_frequency == 0:
            cycle_index = waifu_spawn_order.get(chat_id, 0) % len(rarity_spawn_order)
            rarity = rarity_spawn_order[cycle_index]
            await send_character(update, context, rarity)
            waifu_spawn_order[chat_id] = cycle_index + 1

        if message_counts[chat_id] % 50 == 0:
            await save_message_counts()


# --- Send Character ---
async def send_character(update: Update, context: CallbackContext, rarity: str) -> None:
    chat_id = update.effective_chat.id
    all_characters = list(await collection.find({"rarity": rarity}).to_list(length=None))
    if not all_characters:
        return

    if chat_id in first_correct_guesses and first_correct_guesses[chat_id] is not None:
        last_grabber_id = first_correct_guesses[chat_id]
        last_grabber_user = await user_collection.find_one({'id': last_grabber_id})
        last_grabber_name = last_grabber_user.get('first_name', 'Unknown User') if last_grabber_user else 'Unknown User'
        warning_text = f'⚠ Waifu already grabbed by <a href="tg://user?id={last_grabber_id}">{escape(last_grabber_name)}</a>.\nℹ Wait for a new waifu to appear.'
        await context.bot.send_message(chat_id=chat_id, text=warning_text, parse_mode='HTML')

    character = random.choice(all_characters)
    last_characters[chat_id] = character
    first_correct_guesses[chat_id] = None

    caption_text = """
🪽 A new amazing character has arrived in this chat...
🦋 Use /seal character_name to add them to your harem!
👑 Find out the rarity by sealing!
"""

    try:
        waifu_message[chat_id] = await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption_text,
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to send image. Error: {str(e)}")

    if rarity == "🫧 Royal":
        try:
            await context.bot.send_message(
                chat_id=ROYAL_NOTIFY_USER_ID,
                text=f"👑 A Royal character has spawned!\nCharacter ID: {character.get('id', 'N/A')}",
            )
        except Exception as e:
            LOGGER.error(f"Failed to notify about Royal character: {e}")


# --- Seal Command ---
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses and first_correct_guesses[chat_id] is not None:
        last_grabber_id = first_correct_guesses[chat_id]
        last_grabber_user = await user_collection.find_one({'id': last_grabber_id})
        last_grabber_name = last_grabber_user['first_name'] if last_grabber_user else 'Unknown User'
        await update.message.reply_text(
            f'⚠ Waifu already grabbed by <a href="tg://user?id={last_grabber_id}">{escape(last_grabber_name)}</a>.\nℹ Wait for a new waifu to appear.',
            parse_mode='HTML'
        )
        return

    guess_text = ' '.join(context.args).lower() if context.args else ''
    character = last_characters[chat_id]
    name_parts = character['name'].lower().split()

    if sorted(name_parts) == sorted(guess_text.split()) or any(part == guess_text for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}}, upsert=True)

        keyboard = [[InlineKeyboardButton("See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            f"💫 Congratulations <b>{escape(update.effective_user.first_name)}</b>!\n"
            f"🎗 𝐍𝐚𝐦𝐞 : <b>{character['name']}</b>\n"
            f"🏵 𝐀𝐧𝐢𝐦𝐞 : <b>{character['anime']}</b>\n"
            f"🎮 𝐑𝐚𝐫𝐢𝐭𝐲 : <b>{character['rarity']}</b>\n\n"
            f"🎯 Do /collection to check your amazing character collection 🎳",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("❌ Please write the correct character name... ❌")


# --- Message Count Command ---
async def message_count_cmd(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    count = message_counts.get(chat_id)

    if count is None:
        data = await message_counts_collection.find_one({"chat_id": chat_id})
        count = data["count"] if data else 0

    await update.message.reply_text(f"📨 Total messages counted in this group: {count}")


# --- Main Function ---
def main() -> None:
    application.add_handler(CommandHandler("seal", guess))
    application.add_handler(CommandHandler("messagecount", message_count_cmd))
    application.add_handler(MessageHandler(filters.ALL, message_counter))

    async def startup_tasks():
        await load_message_counts()

    asyncio.get_event_loop().run_until_complete(startup_tasks())
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    Grabberu.start()
    LOGGER.info("Bot started")
    main()
