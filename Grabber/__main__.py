import importlib
import asyncio
import random
import datetime
import re
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
    get_chat_state, track_user_activity, get_active_user_count
)
from Grabber.modules.rarities import RARITY_MAP

# ─── Constants ──────────────────────────────────────────────────────────────
SPECIAL_GROUP_ID = config.SPECIAL_GROUP_ID
ROYAL_NOTIFY_USER_ID = config.ROYAL_NOTIFY_USER_ID

rarity_spawn_order = [RARITY_MAP[1], RARITY_MAP[4], RARITY_MAP[2], RARITY_MAP[3]]
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
    user_id = message.from_user.id
    
    # 1. Track Activity (Sug 2)
    await track_user_activity(chat_id, user_id)

    # 2. Wild Card Logic (Sug 4) - 0.1% chance for Royal on ANY message
    if random.random() < 0.001:
        await send_character(chat_id, "🫧 Royal")
        return

    # Update count in DB
    count = await increment_message_count(chat_id)

    # 3. Golden Hour Logic (Sug 3) - 50% faster spawns during 8-10 PM UTC
    now = datetime.datetime.now(datetime.timezone.utc)
    multiplier = 1.0
    if 20 <= now.hour <= 22:
        multiplier = 0.5

    # Check special thresholds
    for r_name, threshold in special_rarity_thresholds.items():
        if count % int(threshold * multiplier) == 0:
            if r_name == "🫧 Royal" and chat_id != SPECIAL_GROUP_ID:
                continue
            await send_character(chat_id, r_name)
            return

    # Check normal spawn cycle
    # Dynamic Frequency based on Active Users
    active_count = await get_active_user_count(chat_id)
    
    if active_count >= 6:
        base_freq = 50
    elif active_count >= 3:
        base_freq = 75
    else:
        base_freq = await get_chat_frequency(chat_id)

    if count % int(base_freq * multiplier) == 0:
        # 4. Active Presence Rarity Boost (Sug 2)
        idx = await get_spawn_order(chat_id)
        
        if active_count >= 3:
            # Upgrade: If active, pick from Medium to Cosmic instead of just following order
            rarities = [RARITY_MAP[4], RARITY_MAP[2], RARITY_MAP[3], RARITY_MAP[5]]
            rarity = random.choice(rarities)
        else:
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
        "🦋 Use /seal <name> to collect them!\n"
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

async def set_bot_commands(client):
    """Parses HELP_DATA from start module and sets bot commands on Telegram."""
    from Grabber.modules.start import HELP_DATA
    
    commands = []
    # Regex to extract command and description: 🔹 /command <args> - Description
    command_pattern = re.compile(r"🔹\s+/(?P<cmd>\w+)(?:\s+<[^>]+>)*\s+-\s+(?P<desc>.+)")
    
    seen_commands = set()
    
    for category in HELP_DATA.values():
        if "text" in category:
            for line in category["text"].split("\n"):
                match = command_pattern.search(line)
                if match:
                    cmd = match.group("cmd")
                    desc = match.group("desc").strip()
                    
                    if cmd not in seen_commands:
                        # Telegram limit for description is 100 chars
                        commands.append(
                            types.BotCommand(
                                command=cmd,
                                description=desc[:100]
                            )
                        )
                        seen_commands.add(cmd)
    
    # Add standard start command if not present
    if "start" not in seen_commands:
        commands.append(types.BotCommand("start", "Start the bot and get welcome message"))
        
    if commands:
        try:
            await client.set_bot_commands(commands)
            LOGGER.info(f"Successfully registered {len(commands)} commands with Telegram.")
        except Exception as e:
            LOGGER.error(f"Failed to set bot commands: {e}")

async def main():
    """Main entry point using Pyrogram's startup sequence."""
    LOGGER.info("Initializing Seal-Bot...")
    
    # 1. Register background counter in high-priority group
    app.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)
    
    # 2. Load all module commands
    load_plugins()

    # 3. Start client and set commands
    await app.start()
    await set_bot_commands(app)
    LOGGER.info("Bot is now online and active!")
    
    # Block until shutdown
    await idle()
    
    # Graceful stop
    await app.stop()
    LOGGER.info("Bot shut down cleanly.")

if __name__ == "__main__":
    # Use app.run for robust event loop management on all systems (fixes RuntimeError)
    app.run(main())
