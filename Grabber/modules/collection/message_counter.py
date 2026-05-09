import datetime
import random
import time
import logging

from pyrogram import filters, types
from pyrogram.enums import ParseMode

from Grabber import app, config, LOGGER
from Grabber.core.spawns import (get_active_user_count, get_chat_frequency,
                                 get_chat_state, get_spawn_order,
                                 increment_message_count,
                                 increment_spawn_order, send_character,
                                 track_user_activity)
from Grabber.core.waifu import get_or_load_characters
from Grabber.modules.collection.rarities import (ACTIVE_RARITY_WEIGHTS,
                                                 RARITY_WEIGHTS)
from Grabber.modules.gamebot.auction import trigger_auction

# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("Grabber.spawns")

special_rarity_thresholds = {
    "🎞️ AMV": 2500,
    "🎐 Celestial": 2250,
    "💎 Antique": 2000,
    "🫧 Royal": 1750,
    "🔮 Limited Edition": 1500,
    "💮 Exclusive": 1250,
    "💠 Cosmic": 1000,
    "🟡 Legendary": 700,
    "🟠 Rare": 450,
    "🟢 Medium": 250,
    "⚪ Common": 100
}


@app.on_message(filters.group & ~filters.bot, group=1)
async def message_counter_handler(_, message: types.Message):
    """
    Main handler for counting messages and triggering character spawns.
    Tracks user activity, increments chat message counts, and determines
    when a character should be spawned based on thresholds or random chance.
    """
    chat = message.chat
    if not chat or not message.from_user:
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

    state = await get_chat_state(chat_id)
    last_spawn_time = state.get("last_spawn_time", 0)
    current_time = time.time()

    # Prevent spawns if one happened very recently (60s cooldown)
    if current_time - last_spawn_time < 60:
        return

    # HARDENING: Prevent overlapping spawns during active auctions
    from Grabber.database import r as _redis
    if _redis:
        try:
            if await _redis.exists(f"auction:{chat_id}"):
                return
        except Exception:
            from Grabber.database import sessions_collection
            active_auction = await sessions_collection.find_one({"_id": f"auction:{chat_id}"}, projection={"_id": 1})
            if active_auction: return
    else:
        from Grabber.database import sessions_collection
        active_auction = await sessions_collection.find_one({"_id": f"auction:{chat_id}"}, projection={"_id": 1})
        if active_auction: return

    # Small random chance (0.1%) for a Royal spawn regardless of message count
    if random.random() < 0.001:
        SPAWN_LOGGER.info(f"Triggering RANDOM Royal spawn in {chat_id}")
        await send_character(chat_id, "🫧 Royal")
        return

    from Grabber.core.spawn_utils import get_target_spawn_frequency
    target_freq, active_count, multiplier = await get_target_spawn_frequency(chat_id)

    # Check for special rarity milestones
    for r_name, threshold in special_rarity_thresholds.items():
        threshold_int = int(threshold * multiplier)
        if threshold_int > 0 and count % threshold_int == 0:
            SPAWN_LOGGER.info(f"Milestone {r_name} reached at {count} in {chat_id}")
            await send_character(chat_id, r_name)
            return

    # Trigger standard spawn if milestone is reached
    if count % target_freq == 0:
        SPAWN_LOGGER.info(f"Standard spawn triggered in {chat_id} (count={count}, freq={target_freq})")

        # Use different rarity weights if the chat is very active
        if active_count > 10:
            weights_map = ACTIVE_RARITY_WEIGHTS
        else:
            weights_map = RARITY_WEIGHTS

        rarities = list(weights_map.keys())
        weights = list(weights_map.values())

        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

        # REFACTORED: Automated Auction Logic (1% chance for Rare/Legendary)
        if "Rare" in selected_rarity or "Legendary" in selected_rarity:
            if random.random() < 0.01:
                chars = await get_or_load_characters(selected_rarity)
                if chars:
                    char = random.choice(chars)
                    SPAWN_LOGGER.info(f"Triggering AUTOMATED AUCTION for {char['name']} in {chat_id}")
                    await trigger_auction(chat_id, char)
                    await increment_spawn_order(chat_id)
                    return

        await send_character(chat_id, selected_rarity)
        await increment_spawn_order(chat_id)
