import importlib
import asyncio
import random
from typing import Dict

from pyrogram import filters, types, enums, idle
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, LOGGER, collection, config, message_counts_collection
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
    
    # Update count in DB
    count = await increment_message_count(chat_id)

    # Check special thresholds
    for r_name, threshold in special_rarity_thresholds.items():
        if count % threshold == 0:
            if r_name == "🫧 Royal" and chat_id != SPECIAL_GROUP_ID:
                continue
            await send_character(chat_id, r_name)
            return

    # Check normal spawn cycle
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

# ─── Initialization ─────────────────────────────────────────────────────────
def load_plugins():
    for module_name in ALL_MODULES:
        importlib.import_module(f"Grabber.modules.{module_name}")
    LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

async def main():
    """Main entry point using Pyrogram's startup sequence."""
    LOGGER.info("Initializing Seal-Bot (Strict Pyrogram Mode)...")
    
    # 1. Register background counter in high-priority group
    app.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)
    
    # 2. Load all module commands
    load_plugins()

    # 3. Start client and block
    await app.start()
    LOGGER.info("Bot is now online and active!")
    
    # Block until shutdown
    await idle()
    
    # Graceful stop
    await app.stop()
    LOGGER.info("Bot shut down cleanly.")

if __name__ == "__main__":
    # Use app.run for robust event loop management on all systems (fixes RuntimeError)
    app.run(main())
