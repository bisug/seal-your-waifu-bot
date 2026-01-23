import importlib
import asyncio
import random
import signal
from typing import Dict

from pyrogram import filters, types, enums
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, LOGGER, collection, config
)
from Grabber.modules import ALL_MODULES
from Grabber.core.spawns import (
    increment_message_count, get_chat_frequency, 
    set_active_spawn, get_spawn_order, increment_spawn_order,
    get_chat_state
)

# ─── Constants ──────────────────────────────────────────────────────────────
SPECIAL_GROUP_ID = config.SPECIAL_GROUP_ID
ROYAL_NOTIFY_USER_ID = config.ROYAL_NOTIFY_USER_ID

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
    if not chat or not message.from_user:
        return

    chat_id = chat.id
    
    # 1. Update count in DB
    count = await increment_message_count(chat_id)

    # 2. Check special thresholds
    for r_name, threshold in special_rarity_thresholds.items():
        if count % threshold == 0:
            if r_name == "🫧 Royal" and chat_id != SPECIAL_GROUP_ID:
                continue
            await send_character(chat_id, r_name)
            return

    # 3. Check normal spawn cycle
    freq = await get_chat_frequency(chat_id)
    if count % freq == 0:
        idx = await get_spawn_order(chat_id)
        rarity = rarity_spawn_order[idx % len(rarity_spawn_order)]
        await send_character(chat_id, rarity)
        await increment_spawn_order(chat_id)

# ─── Send Character ─────────────────────────────────────────────────────────
async def send_character(chat_id: int, rarity: str):
    chars = await get_or_load_characters(rarity)
    if not chars:
        return

    # Don't spawn if something is already there and not yet caught?
    # Actually, we let new ones overwrite old ones for speed.
    state = await get_chat_state(chat_id)
    if state.get("last_character") and state.get("first_correct_guess") is None:
        # Optional: could skip or notify
        pass

    character = random.choice(chars)

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
        # Persistent link: Store in DB
        await set_active_spawn(chat_id, character, msg.id)
        
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
    LOGGER.info("Starting bot (Persistent Mode)...")
    
    # Register core handlers
    app.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)
    
    # Load all feature modules
    load_plugins()

    async with app:
        LOGGER.info("Bot is now online!")
        stop_event = asyncio.Event()
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, AttributeError):
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
