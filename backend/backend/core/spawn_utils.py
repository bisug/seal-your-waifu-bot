from backend.core.spawns import get_active_user_count, get_chat_frequency, is_golden_hour


async def get_target_spawn_frequency(chat_id: int):
    """
    Calculates the target message frequency for spawns based on chat activity.
    Returns (target_freq, active_count, multiplier).
    """
    active_count = await get_active_user_count(chat_id)
    if active_count >= 6:
        base_freq = 40
    elif active_count >= 3:
        base_freq = 60
    else:
        freq = await get_chat_frequency(chat_id)
        base_freq = min(freq, 80) if freq is not None else 80
    # Check for "Golden Hour" (boosted spawn rates)
    multiplier = 0.5 if is_golden_hour() else 1.0
    target_freq = max(1, int(base_freq * multiplier))
    return target_freq, active_count, multiplier
