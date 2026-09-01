"""Guards for spawn-pipeline optimizations.

1. send_character must skip automatic spawns while a recent spawn is still
   unclaimed (previously a new spawn silently replaced the old character,
   making it uncatchable), but force=True (/cnow) must bypass the guard.
2. is_golden_hour must match the 20:00-22:59 UTC window used by the
   frequency multiplier and milestone thresholds.
3. Golden-hour milestone thresholds must be exactly half the normal ones
   (min 1), so milestones are reached 2x faster during Golden Hour.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.core import spawns
from backend.modules.collection import message_counter


@pytest.mark.asyncio
async def test_send_character_skips_while_spawn_unclaimed():
    state = {
        "last_character": {"name": "Test Waifu", "rarity": "⚪ Common"},
        "last_spawn_time": spawns.time.time() - 10,  # 10s ago: inside grace window
    }
    with patch.object(spawns, "get_chat_state", AsyncMock(return_value=state)):
        with patch.object(spawns, "get_or_load_characters", AsyncMock()) as load:
            await spawns.send_character(-100123, "⚪ Common")

    load.assert_not_awaited()  # Guard tripped: no character loaded or sent


@pytest.mark.asyncio
async def test_send_character_forces_past_guard():
    state = {
        "last_character": {"name": "Test Waifu", "rarity": "⚪ Common"},
        "last_spawn_time": spawns.time.time() - 10,
    }
    sent = asyncio.Event()

    async def fake_send(*args, **kwargs):
        sent.set()
        return None

    with patch.object(spawns, "get_chat_state", AsyncMock(return_value=state)):
        with patch.object(spawns, "get_or_load_characters", AsyncMock(return_value=[{"name": "X", "img_url": "u"}])):
            with patch.object(spawns.app, "send_media_safe", AsyncMock(side_effect=fake_send)):
                await spawns.send_character(-100123, "⚪ Common", force=True)

    assert sent.is_set()  # /cnow path ignores the unclaimed-spawn guard


@pytest.mark.asyncio
async def test_send_character_allows_after_grace_expiry():
    state = {
        "last_character": {"name": "Test Waifu", "rarity": "⚪ Common"},
        "last_spawn_time": spawns.time.time() - spawns.ACTIVE_SPAWN_GRACE_SECONDS - 5,
    }
    sent = asyncio.Event()

    async def fake_send(*args, **kwargs):
        sent.set()
        return None

    with patch.object(spawns, "get_chat_state", AsyncMock(return_value=state)):
        with patch.object(spawns, "get_or_load_characters", AsyncMock(return_value=[{"name": "X", "img_url": "u"}])):
            with patch.object(spawns.app, "send_media_safe", AsyncMock(side_effect=fake_send)):
                await spawns.send_character(-100123, "⚪ Common")

    assert sent.is_set()  # Stale spawn (5+ min unclaimed) gets replaced


def test_golden_hour_window():
    import datetime

    make = lambda h: datetime.datetime(2026, 9, 1, h, 0, tzinfo=datetime.timezone.utc)
    assert spawns.is_golden_hour(make(20)) is True
    assert spawns.is_golden_hour(make(22)) is True
    assert spawns.is_golden_hour(make(23)) is False
    assert spawns.is_golden_hour(make(19)) is False
    assert spawns.is_golden_hour(make(3)) is False


def test_golden_milestones_are_half():
    for (name, normal), (gname, golden) in zip(
        message_counter._MILESTONES, message_counter._MILESTONES_GOLDEN
    ):
        assert name == gname
        assert golden == max(1, normal // 2)
