import logging
import random

from pyrogram import filters, types

from backend.client import app
from backend.core.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    MILESTONE_THRESHOLDS,
    RARITY_MAP,
    SPAWN_RARITY_WEIGHTS,
    weighted_pick,
)
from backend.core.spawn_utils import get_target_spawn_frequency
from backend.core.spawns import (
    increment_message_count,
    send_character,
    track_user_activity,
)

# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("backend.spawns")
RANDOM_ROYAL_SPAWN_CHANCE = 0.0002
# Milestone thresholds live in the `rarities` collection (per-doc `milestone`
# field, editable via /rarityset). Keyed by rarity_id, resolved to labels at
# import — rarity_id survives /rarityrename, so a rename can't orphan a
# milestone.


def _build_milestones() -> tuple:
    """(label, threshold) pairs for configured rarities, highest threshold first."""
    pairs = [
        (RARITY_MAP[rid], threshold)
        for rid, threshold in MILESTONE_THRESHOLDS.items()
        if rid in RARITY_MAP
    ]
    return tuple(sorted(pairs, key=lambda p: -p[1]))


_MILESTONES = _build_milestones()


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
    # Check for special rarity milestones
    milestones = _MILESTONES
    for r_name, threshold in milestones:
        if threshold > 0 and count % threshold == 0:
            SPAWN_LOGGER.info(f"Milestone {r_name} reached at {count} in {chat_id}")
            await send_character(chat_id, r_name)
            return
    # Standard spawn logic — frequency resolved by the shared helper
    target_freq, active_count = await get_target_spawn_frequency(chat_id)
    if count % target_freq == 0:
        SPAWN_LOGGER.info(f"Standard spawn triggered in {chat_id} (count={count}, freq={target_freq})")
        selected_rarity = _pick_spawn_rarity(active_count)
        if selected_rarity:
            await send_character(chat_id, selected_rarity)
