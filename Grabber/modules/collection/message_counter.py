import datetime
import random
import time
import logging
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import app, config, LOGGER
from Grabber.core.spawns import (get_active_user_count, get_chat_frequency,
                                 get_chat_state, get_spawn_order,
                                 increment_message_count,
                                 increment_spawn_order, send_character,
                                 track_user_activity)
from Grabber.core.waifu import get_or_load_characters
from Grabber.modules.collection.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    SPAWN_RARITY_WEIGHTS,
)
# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("Grabber.spawns")
RANDOM_ROYAL_SPAWN_CHANCE = 0.0002
special_rarity_thresholds = {
    "🌠 Astral": 10000,
    "🪽 Prestige": 9000,
    "✨ Divine": 8500,
    "🎞️ AMV": 8000,
    "🎐 Celestial": 7500,
    "💎 Mythical": 7000,
    "💎 Antique": 6500,
    "🫧 Royal": 6000,
    "🔮 Mystic": 5500,
    "🔮 Limited Edition": 5000,
    "🌌 Eternal": 4500,
    "💮 Exclusive": 4000,
    "🧬 Immortal": 3500,
    "💠 Cosmic": 3200,
    "🟡 Legendary": 2000,
    "🟠 Rare": 1200,
    "🟣 Epic": 700,
    "🟢 Medium": 350,
    "⚪ Common": 150,
}
@app.on_message(filters.group & filters.text & ~filters.bot, group=1)
async def message_counter_handler(_, message: types.Message):
    """
    Main handler for counting messages and triggering character spawns.
    Tracks user activity, increments chat message counts, and determines
    when a character should be spawned based on thresholds or random chance.
    """
    chat = message.chat
    if not chat or not message.from_user:
        return
    if getattr(message.from_user, "is_bot", False):
        return
    if not message.text:
        return
    chat_id = chat.id
    user_id = message.from_user.id
    # Track activity to determine chat "busyness"
    await track_user_activity(chat_id, user_id)
    # Increment and get the current message count for this chat
    count = await increment_message_count(chat_id, user_id)
    # Debug logging for every 10th message to avoid spam but show activity
    if count % 10 == 0:
        SPAWN_LOGGER.info(f"Chat {chat_id} reached {count} messages.")
    # Small random chance (0.02%) for a Royal spawn regardless of message count
    if random.random() < RANDOM_ROYAL_SPAWN_CHANCE:
        SPAWN_LOGGER.info(f"Triggering RANDOM Royal spawn in {chat_id}")
        await send_character(chat_id, "🫧 Royal")
        return
    # Check for "Golden Hour" (boosted spawn rates)
    now = datetime.datetime.now(datetime.timezone.utc)
    multiplier = 1.0
    if 20 <= now.hour <= 22:
        multiplier = 0.5 # Milestones reached twice as fast
    # Check for special rarity milestones
    for r_name, threshold in special_rarity_thresholds.items():
        threshold_int = int(threshold * multiplier)
        if threshold_int > 0 and count % threshold_int == 0:
            SPAWN_LOGGER.info(f"Milestone {r_name} reached at {count} in {chat_id}")
            await send_character(chat_id, r_name)
            return
    # Standard spawn logic based on chat activity levels
    active_count = await get_active_user_count(chat_id)
    if active_count >= 6:
        base_freq = 40
    elif active_count >= 3:
        base_freq = 60
    else:
        freq = await get_chat_frequency(chat_id)
        base_freq = min(freq, 80) if freq is not None else 80
    # Trigger standard spawn if milestone is reached
    base_freq_int = max(1, int(base_freq * multiplier))
    if count % base_freq_int == 0:
        SPAWN_LOGGER.info(f"Standard spawn triggered in {chat_id} (count={count}, freq={base_freq_int})")
        # Use different rarity weights if the chat is very active
        if active_count > 10:
            weights_map = ACTIVE_SPAWN_RARITY_WEIGHTS
        else:
            weights_map = SPAWN_RARITY_WEIGHTS
        rarities = list(weights_map.keys())
        weights = list(weights_map.values())
        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]
        await send_character(chat_id, selected_rarity)
        await increment_spawn_order(chat_id)
