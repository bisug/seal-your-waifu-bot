import datetime
import random
import time

from pyrogram import types

from Grabber import config
from Grabber.core.spawns import (get_active_user_count, get_chat_frequency,
                                 get_chat_state, get_spawn_order,
                                 increment_message_count,
                                 increment_spawn_order, send_character,
                                 track_user_activity)
from Grabber.core.waifu import get_or_load_characters
from Grabber.modules.collection.rarities import (ACTIVE_RARITY_WEIGHTS,
                                                 RARITY_WEIGHTS)
from Grabber.modules.gamebot.auction import trigger_auction

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


async def message_counter(_, message: types.Message):
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
    count = await increment_message_count(chat_id)



    state = await get_chat_state(chat_id)
    last_spawn_time = state.get("last_spawn_time", 0)
    current_time = time.time()

    # Prevent spawns if one happened very recently
    if current_time - last_spawn_time < 60:
        return

    # HARDENING: Prevent overlapping spawns during active auctions
    from Grabber.database import sessions_collection
    active_auction = await sessions_collection.find_one({"_id": f"auction:{chat_id}"})
    if active_auction:
        return

    # Small random chance for a Royal spawn regardless of message count
    if random.random() < 0.001:
        await send_character(chat_id, "🫧 Royal")
        return


    # Check for "Golden Hour" (boosted spawn rates)
    now = datetime.datetime.now(datetime.timezone.utc)
    multiplier = 1.0
    if 20 <= now.hour <= 22:
        multiplier = 0.5

    # Check for special rarity milestones (e.g., every 300th message)
    for r_name, threshold in special_rarity_thresholds.items():
        threshold_int = int(threshold * multiplier)
        if threshold_int > 0 and count % threshold_int == 0:
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
        # Use different rarity weights if the chat is very active
        if active_count > 10:
            weights_map = ACTIVE_RARITY_WEIGHTS
        else:
            weights_map = RARITY_WEIGHTS

        rarities = list(weights_map.keys())
        weights = list(weights_map.values())

        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

        # REFACTORED: Automated Auction Logic
        # Auctions have a 1% chance to trigger for Rare or Legendary characters.
        if "Rare" in selected_rarity or "Legendary" in selected_rarity:
            if random.random() < 0.01:
                # Fetch a random character of this rarity
                chars = await get_or_load_characters(selected_rarity)
                if chars:
                    char = random.choice(chars)
                    await trigger_auction(chat_id, char)
                    await increment_spawn_order(chat_id)
                    return

        await send_character(chat_id, selected_rarity)
        await increment_spawn_order(chat_id)
