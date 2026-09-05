import asyncio
import logging
import random

from pyrogram import filters, types

from backend.client import app
from backend.core.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    SPAWN_RARITY_WEIGHTS,
    weighted_pick,
)
from backend.core.spawn_utils import get_target_spawn_frequency
from backend.core.spawns import (
    _next_pokemon_spawn_slot,
    get_active_pokemon_spawn,
    increment_message_count,
    send_character,
    send_pokemon_spawn,
    track_user_activity,
)

# Use a specific logger for spawn tracking
SPAWN_LOGGER = logging.getLogger("backend.spawns")
RANDOM_ROYAL_SPAWN_CHANCE = 0.0002


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
    Every Nth spawn is a guess-the-Pokémon minigame instead.
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
    # Activity tracking and message counting hit different Redis keys — run
    # both pipelines concurrently so two round trips cost one wall-clock hop.
    _, count = await asyncio.gather(
        track_user_activity(chat_id, user_id),
        increment_message_count(chat_id, user_id),
    )
    # Debug logging for every 10th message to avoid spam but show activity
    if count % 10 == 0:
        SPAWN_LOGGER.info(f"Chat {chat_id} reached {count} messages.")
    # Small random chance (0.02%) for a Royal spawn regardless of message count
    if random.random() < RANDOM_ROYAL_SPAWN_CHANCE:
        SPAWN_LOGGER.info(f"Triggering RANDOM Royal spawn in {chat_id}")
        await send_character(chat_id, "🫧 Royal")
        return
    # Standard spawn logic — frequency resolved by the shared helper
    target_freq, active_count = await get_target_spawn_frequency(chat_id)
    if count % target_freq == 0:
        # Every Nth spawn is a Pokémon guessing game (if none is active).
        if await _next_pokemon_spawn_slot(chat_id):
            if not await get_active_pokemon_spawn(chat_id):
                SPAWN_LOGGER.info(f"Pokémon spawn triggered in {chat_id} (count={count})")
                await send_pokemon_spawn(chat_id)
                return
        SPAWN_LOGGER.info(f"Standard spawn triggered in {chat_id} (count={count}, freq={target_freq})")
        selected_rarity = _pick_spawn_rarity(active_count)
        if selected_rarity:
            await send_character(chat_id, selected_rarity)
