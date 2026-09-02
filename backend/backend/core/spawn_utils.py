from backend.core.spawns import get_active_user_count, get_chat_frequency


async def get_target_spawn_frequency(chat_id: int):
    """
    Calculates the target message frequency for spawns based on chat activity.
    Returns (target_freq, active_count).
    """
    active_count = await get_active_user_count(chat_id)
    if active_count >= 6:
        base_freq = 40
    elif active_count >= 3:
        base_freq = 60
    else:
        freq = await get_chat_frequency(chat_id)
        base_freq = min(freq, 80) if freq is not None else 80
    return max(1, base_freq), active_count
