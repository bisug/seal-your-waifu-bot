import importlib
import asyncio
import random
import signal
from html import escape
from typing import Optional, Dict, Any

from pyrogram import filters, types, enums
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, LOGGER, collection, message_counts_collection, 
    user_collection, user_totals_collection, config
)
from Grabber.modules import ALL_MODULES

# ─── Constants ──────────────────────────────────────────────────────────────
SPECIAL_GROUP_ID = config.SPECIAL_GROUP_ID
ROYAL_NOTIFY_USER_ID = config.ROYAL_NOTIFY_USER_ID

# ─── Globals ────────────────────────────────────────────────────────────────
locks: Dict[str, asyncio.Lock] = {}
message_counts: Dict[str, int] = {}
waifu_spawn_order: Dict[str, int] = {}
last_characters: Dict[int, dict] = {}
first_correct_guesses: Dict[int, Optional[int]] = {}
waifu_message: Dict[int, Any] = {}

rarity_spawn_order = ["⚪ Common", "🟢 Medium", "🟠 Rare", "🟡 Legendary"]
special_rarity_thresholds = {
    "💠 Cosmic": 300,
    "💮 Exclusive": 600,
    "🔮 Limited Edition": 900,
    "🫧 Royal": 1000
}

characters_by_rarity: Dict[str, list] = {}

# ─── Utils ──────────────────────────────────────────────────────────────────
async def get_or_load_characters(rarity: str) -> list:
    if rarity not in characters_by_rarity:
        cursor = collection.find({"rarity": rarity})
        chars = await cursor.to_list(length=None)
        random.shuffle(chars)
        characters_by_rarity[rarity] = chars
    return characters_by_rarity[rarity]

# ─── Message Counter ────────────────────────────────────────────────────────
async def message_counter(_, message: types.Message):
    chat = message.chat
    user = message.from_user
    if not user or not chat:
        return

    chat_id_str = str(chat.id)
    chat_id_int = chat.id

    if chat_id_str not in locks:
        locks[chat_id_str] = asyncio.Lock()

    async with locks[chat_id_str]:
        if chat_id_str not in message_counts:
            doc = await message_counts_collection.find_one({"chat_id": chat_id_str})
            message_counts[chat_id_str] = doc["count"] if doc else 0

        count = message_counts[chat_id_str] + 1
        message_counts[chat_id_str] = count

        chat_settings = await user_totals_collection.find_one(
            {"chat_id": chat_id_str},
            projection={"message_frequency": 1}
        )
        freq = chat_settings.get("message_frequency", 100) if chat_settings else 100

        # Special rarity check
        for r_name, threshold in special_rarity_thresholds.items():
            if count % threshold == 0:
                if r_name == "🫧 Royal" and chat_id_int != SPECIAL_GROUP_ID:
                    continue
                await send_character(chat_id_int, r_name)
                return

        # Normal cycle spawn
        if count % freq == 0:
            idx = waifu_spawn_order.get(chat_id_str, 0) % len(rarity_spawn_order)
            rarity = rarity_spawn_order[idx]
            await send_character(chat_id_int, rarity)
            waifu_spawn_order[chat_id_str] = idx + 1

        # Periodic save
        if count % 50 == 0:
            await message_counts_collection.update_one(
                {"chat_id": chat_id_str},
                {"$set": {"count": count}},
                upsert=True
            )

# ─── Send Character ─────────────────────────────────────────────────────────
async def send_character(chat_id: int, rarity: str):
    chars = await get_or_load_characters(rarity)
    if not chars:
        return

    if chat_id in first_correct_guesses and first_correct_guesses[chat_id] is not None:
        return

    character = random.choice(chars)
    last_characters[chat_id] = character
    first_correct_guesses[chat_id] = None

    caption = (
        "🪽 **A new character appeared!**\n"
        "🦋 Use `/seal <name>` to collect them!\n"
        "👑 Rarity is secret until caught!"
    )

    try:
        await app.send_chat_action(chat_id, enums.ChatAction.UPLOAD_PHOTO)
        msg = await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        waifu_message[chat_id] = msg
    except Exception as e:
        LOGGER.error(f"Error sending character: {e}")

    if rarity == "🫧 Royal":
        try:
            await app.send_message(
                ROYAL_NOTIFY_USER_ID,
                f"👑 **Royal Spawn!**\nID: `{character['id']}`\nName: {character['name']}"
            )
        except Exception:
            pass

# ─── Load Modules ───────────────────────────────────────────────────────────
def load_plugins():
    for module_name in ALL_MODULES:
        importlib.import_module(f"Grabber.modules.{module_name}")
    LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

async def main():
    # Pre-startup tasks
    LOGGER.info("Starting bot...")
    
    # Load counts from DB
    async for doc in message_counts_collection.find({}):
        message_counts[str(doc["chat_id"])] = doc["count"]
    
    # Register core handlers
    app.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])))
    
    # Load all feature modules
    load_plugins()

    async with app:
        LOGGER.info("Bot is now online!")
        # Use an event to handle shutdown gracefully
        stop_event = asyncio.Event()
        
        # Signal handlers for Unix-like systems
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, AttributeError):
            # Windows or alternative loop support
            pass

        try:
            await stop_event.wait()
        except KeyboardInterrupt:
            pass
        
        LOGGER.info("Shutdown signal received. Cleaning up...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
