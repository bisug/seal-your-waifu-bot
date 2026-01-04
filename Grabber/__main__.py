import importlib
import asyncio
import random
from html import escape
from typing import Optional, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from Grabber import (
    collection, db, user_collection, message_counts_collection,
    application, LOGGER, user_totals_collection, Grabberu
)
from Grabber.modules import ALL_MODULES

# ─── Constants ──────────────────────────────────────────────────────────────
SPECIAL_GROUP_ID = -1002528887253    # Royal spawns only here
ROYAL_NOTIFY_USER_ID = 7717913705    # Send royal info to this user

# ─── Globals ────────────────────────────────────────────────────────────────
locks: Dict[str, asyncio.Lock] = {}
message_counts: Dict[str, int] = {}
waifu_spawn_order: Dict[str, int] = {}
last_characters: Dict[int, dict] = {}
first_correct_guesses: Dict[int, Optional[int]] = {}
waifu_message: Dict[int, Any] = {}
# warned_users  ← currently unused → can be removed if not planned to be used

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

# Preload characters per rarity (big optimization!)
characters_by_rarity: Dict[str, list] = {}

# ─── Module Loader ──────────────────────────────────────────────────────────
for module_name in ALL_MODULES:
    importlib.import_module(f"Grabber.modules.{module_name}")


# ─── Utils ──────────────────────────────────────────────────────────────────
async def get_or_load_characters(rarity: str) -> list:
    """Cache characters per rarity - huge performance gain"""
    if rarity not in characters_by_rarity:
        chars = await collection.find({"rarity": rarity}).to_list(None)
        random.shuffle(chars)  # shuffle once → faster random.choice later
        characters_by_rarity[rarity] = chars
    return characters_by_rarity[rarity]


# ─── Message Counter (main hot path) ────────────────────────────────────────
async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not user or not chat:
        return

    chat_id_str = str(chat.id)
    chat_id_int = chat.id

    # Fast path — lock only when needed
    if chat_id_str not in locks:
        locks[chat_id_str] = asyncio.Lock()

    async with locks[chat_id_str]:
        # Lazy load count
        if chat_id_str not in message_counts:
            doc = await message_counts_collection.find_one({"chat_id": chat_id_str})
            message_counts[chat_id_str] = doc["count"] if doc else 0

        count = message_counts[chat_id_str] + 1
        message_counts[chat_id_str] = count

        # Get frequency once
        chat_settings = await user_totals_collection.find_one(
            {"chat_id": chat_id_str},
            projection={"message_frequency": 1}
        )
        freq = chat_settings.get("message_frequency", 100) if chat_settings else 100

        # ── Special rarity check first (most rare → should be fast path) ──
        for r_name, threshold in special_rarity_thresholds.items():
            if count % threshold == 0:
                if r_name == "🫧 Royal" and chat_id_int != SPECIAL_GROUP_ID:
                    continue
                await send_character(chat_id_int, context, r_name)
                # We return early → no normal spawn in the same message
                return

        # ── Normal cycle spawn ─────────────────────────────────────────────
        if count % freq == 0:
            idx = waifu_spawn_order.get(chat_id_str, 0) % len(rarity_spawn_order)
            rarity = rarity_spawn_order[idx]
            await send_character(chat_id_int, context, rarity)
            waifu_spawn_order[chat_id_str] = idx + 1

        # Batch save every 50 messages (still)
        if count % 50 == 0:
            await message_counts_collection.update_one(
                {"chat_id": chat_id_str},
                {"$set": {"count": count}},
                upsert=True
            )


# ─── Send Character ─────────────────────────────────────────────────────────
async def send_character(chat_id: int, context: ContextTypes.DEFAULT_TYPE, rarity: str) -> None:
    chars = await get_or_load_characters(rarity)
    if not chars:
        return

    if chat_id in first_correct_guesses and first_correct_guesses[chat_id] is not None:
        last_id = first_correct_guesses[chat_id]
        user_doc = await user_collection.find_one(
            {'id': last_id},
            projection={'first_name': 1}
        )
        name = user_doc.get('first_name', 'Unknown') if user_doc else 'Unknown'
        text = (
            f'⚠ Waifu already grabbed by <a href="tg://user?id={last_id}">{escape(name)}</a>.\n'
            f'ℹ Wait for a new waifu to appear.'
        )
        await context.bot.send_message(chat_id, text, parse_mode='HTML')
        return  # ← early return, prevents sending new character

    character = random.choice(chars)
    last_characters[chat_id] = character
    first_correct_guesses[chat_id] = None

    caption = (
        "🪽 A new amazing character has arrived in this chat...\n"
        "🦋 Use /seal character_name to add them to your harem!\n"
        "👑 Find out the rarity by sealing!"
    )

    try:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode='HTML'
        )
        waifu_message[chat_id] = msg
    except Exception as e:
        LOGGER.error(f"Failed to send waifu photo: {e}", exc_info=True)

    # Royal notification
    if rarity == "🫧 Royal":
        try:
            await context.bot.send_message(
                ROYAL_NOTIFY_USER_ID,
                f"👑 A Royal character has spawned!\nCharacter ID: {character.get('id', 'N/A')}"
            )
        except Exception as e:
            LOGGER.error(f"Royal notification failed: {e}")


# ─── Seal / Guess ───────────────────────────────────────────────────────────
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses and first_correct_guesses[chat_id] is not None:
        last_id = first_correct_guesses[chat_id]
        user_doc = await user_collection.find_one(
            {'id': last_id},
            projection={'first_name': 1}
        )
        name = user_doc.get('first_name', 'Unknown') if user_doc else 'Unknown'
        await update.message.reply_text(
            f'⚠ Waifu already grabbed by <a href="tg://user?id={last_id}">{escape(name)}</a>.\n'
            f'ℹ Wait for a new waifu to appear.',
            parse_mode='HTML'
        )
        return

    if not context.args:
        return

    guess_text = ' '.join(context.args).lower()
    character = last_characters[chat_id]

    name_parts = character['name'].lower().split()

    # Fast check
    if (sorted(name_parts) == sorted(guess_text.split()) or
            any(part == guess_text for part in name_parts)):
        first_correct_guesses[chat_id] = user.id

        await user_collection.update_one(
            {'id': user.id},
            {'$push': {'characters': character}},
            upsert=True
        )

        keyboard = [[InlineKeyboardButton(
            "See Harem",
            switch_inline_query_current_chat=f"collection.{user.id}"
        )]]

        await update.message.reply_text(
            f"💫 Congratulations <b>{escape(user.first_name)}</b>!\n"
            f"🎗 𝐍𝐚𝐦𝐞 : <b>{character['name']}</b>\n"
            f"🏵 𝐀𝐧𝐢𝐦𝐞 : <b>{character['anime']}</b>\n"
            f"🎮 𝐑𝐚𝐫𝐢𝐭𝐲 : <b>{character['rarity']}</b>\n\n"
            f"🎯 Do /collection to check your amazing character collection 🎳",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ─── Message Count Command ──────────────────────────────────────────────────
async def message_count_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id_str = str(update.effective_chat.id)
    count = message_counts.get(chat_id_str)

    if count is None:
        doc = await message_counts_collection.find_one({"chat_id": chat_id_str})
        count = doc["count"] if doc else 0

    await update.message.reply_text(f"📨 Total messages counted in this group: {count}")


async def post_init(app: Application) -> None:
    await load_message_counts()


async def load_message_counts():
    async for doc in message_counts_collection.find({}):
        message_counts[str(doc["chat_id"])] = doc["count"]


def main():
    application.add_handler(CommandHandler("seal", guess))
    application.add_handler(CommandHandler("messagecount", message_count_cmd))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_counter))

    application.post_init = post_init
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    Grabberu.start()
    LOGGER.info("Bot started")
    main()
