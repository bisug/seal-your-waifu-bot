import random
import datetime
import time
from pyrogram import types
from Grabber import config
from Grabber.core.spawns import (
    increment_message_count, get_chat_frequency,
    send_character, get_spawn_order, increment_spawn_order,
    get_chat_state, track_user_activity, get_active_user_count
)
from Grabber.modules.collection.rarities import RARITY_WEIGHTS, ACTIVE_RARITY_WEIGHTS

SPECIAL_GROUP_ID = config.SPECIAL_GROUP_ID

special_rarity_thresholds = {
    "💠 Cosmic": 300,
    "💮 Exclusive": 600,
    "🔮 Limited Edition": 900,
    "🫧 Royal": 1000
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
        if count % int(threshold * multiplier) == 0:
            if r_name == "🫧 Royal" and chat_id != SPECIAL_GROUP_ID:
                continue
            await send_character(chat_id, r_name)
            return



    # Standard spawn logic based on chat activity levels
    active_count = await get_active_user_count(chat_id)

    if active_count >= 6:
        base_freq = 50
    elif active_count >= 3:
        base_freq = 75
    else:
        freq = await get_chat_frequency(chat_id)
        base_freq = freq if freq is not None else 100

    # Trigger standard spawn if milestone is reached
    if count % int(base_freq * multiplier) == 0:
        # Use different rarity weights if the chat is very active
        if active_count > 10:
            weights_map = ACTIVE_RARITY_WEIGHTS
        else:
            weights_map = RARITY_WEIGHTS

        rarities = list(weights_map.keys())
        weights = list(weights_map.values())

        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

        await send_character(chat_id, selected_rarity)


        await increment_spawn_order(chat_id)
