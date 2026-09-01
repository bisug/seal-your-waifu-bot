import logging
import random
from pyrogram import filters, types

from backend import app
from backend.core.spawn_utils import get_target_spawn_frequency
from backend.core.spawns import (increment_message_count,
                                 is_golden_hour,
                                 send_character,
                                 track_user_activity)
from backend.modules.collection.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    SPAWN_RARITY_WEIGHTS,
)
# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("backend.spawns")
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
# Precomputed (rarity, threshold) pairs — avoids rebuilding the list on every
# message. Golden Hour halves thresholds (milestones reached 2x faster).
_MILESTONES = tuple(special_rarity_thresholds.items())
_MILESTONES_GOLDEN = tuple(
    (name, max(1, threshold // 2)) for name, threshold in _MILESTONES
)


def _pick_spawn_rarity(active_count: int) -> str:
    """Weighted rarity pick; very active chats use the active-weights table."""
    weights_map = ACTIVE_SPAWN_RARITY_WEIGHTS if active_count > 10 else SPAWN_RARITY_WEIGHTS
    rarities = list(weights_map.keys())
    weights = list(weights_map.values())
    return random.choices(rarities, weights=weights, k=1)[0]
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
    # Check for special rarity milestones (Golden Hour halves thresholds)
    milestones = _MILESTONES_GOLDEN if is_golden_hour() else _MILESTONES
    for r_name, threshold in milestones:
        if threshold > 0 and count % threshold == 0:
            SPAWN_LOGGER.info(f"Milestone {r_name} reached at {count} in {chat_id}")
            await send_character(chat_id, r_name)
            return
    # Standard spawn logic — frequency/multiplier resolved by the shared helper
    target_freq, active_count, _ = await get_target_spawn_frequency(chat_id)
    if count % target_freq == 0:
        SPAWN_LOGGER.info(f"Standard spawn triggered in {chat_id} (count={count}, freq={target_freq})")
        await send_character(chat_id, _pick_spawn_rarity(active_count))
