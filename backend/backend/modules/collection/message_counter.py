import logging
import random
from pyrogram import filters, types
from backend import app
from backend.core.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    SPAWN_RARITY_WEIGHTS,
    weighted_pick,
)
from backend.core.spawn_utils import get_target_spawn_frequency
from backend.core.spawns import (increment_message_count,
                                 is_golden_hour,
                                 send_character,
                                 track_user_activity)
# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("backend.spawns")
RANDOM_ROYAL_SPAWN_CHANCE = 0.0002
# Milestone thresholds keyed by rarity_id, resolved to labels at import.
# rarity_id survives /rarityrename (labels don't), so a rename can no longer
# silently orphan a milestone. Golden Hour halves thresholds (2x faster).
_RARITY_MILESTONE_THRESHOLDS = {
    25: 10000,  # 🌠 Astral
    12: 9000,   # 🪽 Prestige
    24: 8500,   # ✨ Divine
    11: 8000,   # 🎞️ AMV
    10: 7500,   # 🎐 Celestial
    23: 7000,   # 💎 Mythical
    9: 6500,    # 💎 Antique
    8: 6000,    # 🫧 Royal
    22: 5500,   # 🔮 Mystic
    7: 5000,    # 🔮 Limited Edition
    21: 4500,   # 🌌 Eternal
    6: 4000,    # 💮 Exclusive
    20: 3500,   # 🧬 Immortal
    5: 3200,    # 💠 Cosmic
    4: 2000,    # 🟡 Legendary
    3: 1200,    # 🟠 Rare
    19: 700,    # 🟣 Epic
    2: 350,     # 🟢 Medium
    1: 150,     # ⚪ Common
}
from backend.core.rarities import RARITY_MAP


def _build_milestones() -> tuple:
    """(label, threshold) pairs for configured rarities, highest threshold first."""
    pairs = [
        (RARITY_MAP[rid], threshold)
        for rid, threshold in _RARITY_MILESTONE_THRESHOLDS.items()
        if rid in RARITY_MAP
    ]
    return tuple(sorted(pairs, key=lambda p: -p[1]))


_MILESTONES = _build_milestones()
_MILESTONES_GOLDEN = tuple(
    (label, max(1, threshold // 2)) for label, threshold in _MILESTONES
)


def _pick_spawn_rarity(active_count: int) -> str | None:
    """Weighted rarity pick; very active chats use the active-weights table."""
    weights_map = ACTIVE_SPAWN_RARITY_WEIGHTS if active_count > 10 else SPAWN_RARITY_WEIGHTS
    return weighted_pick(weights_map)
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
        selected_rarity = _pick_spawn_rarity(active_count)
        if selected_rarity:
            await send_character(chat_id, selected_rarity)
