"""Regression tests for spawn/reward variety: recent-exclusion picking.

Guards the "same character spawned/rewarded repeatedly" bug:
1. _pick_excluding never returns an id on the recent list (when avoidable).
2. Tiny pools fall back to the full list instead of failing.
3. Empty recent list behaves like plain random.choice.
4. sample_character_by_rarity with a user_id excludes that user's recent
   rewards and records the pick (per-user variety for /daily, /claim,
   /propose, egg hatches, free spins).
"""
import random
from unittest.mock import AsyncMock, patch

import pytest

from backend.core import waifu
from backend.core.waifu import _pick_excluding, sample_character_by_rarity

POOL = [{"id": f"c{i}", "name": f"Char {i}"} for i in range(20)]


def test_pick_avoids_recent_ids():
    recent = ["c0", "c1", "c2"]
    for _ in range(50):
        pick = _pick_excluding(POOL, recent)
        assert str(pick["id"]) not in recent


def test_tiny_pool_falls_back():
    tiny = [{"id": "only"}, {"id": "only2"}]
    recent = ["only", "only2"]
    # Everything excluded -> must still return something from the pool.
    pick = _pick_excluding(tiny, recent)
    assert pick in tiny


def test_empty_recent_is_plain_choice():
    random.seed(42)
    expected = random.choice(POOL)
    random.seed(42)
    assert _pick_excluding(POOL, []) == expected


def test_single_char_pool():
    solo = [{"id": "solo"}]
    assert _pick_excluding(solo, ["solo"]) == solo[0]


@pytest.mark.asyncio
async def test_sample_excludes_user_recent_rewards():
    pool = [{"id": f"c{i}", "name": f"Char {i}"} for i in range(30)]
    recent = ["c0", "c1", "c2", "c3"]
    with patch.object(waifu, "get_or_load_characters", AsyncMock(return_value=pool)):
        with patch.object(waifu, "_get_recent_reward_ids", AsyncMock(return_value=recent)):
            with patch.object(waifu, "_record_recent_reward", AsyncMock()) as record:
                for _ in range(50):
                    pick = await sample_character_by_rarity("⚪ Common", user_id=42)
                    assert str(pick["id"]) not in recent
                record.assert_awaited()  # pick is remembered for next time


@pytest.mark.asyncio
async def test_sample_without_user_id_is_plain_choice():
    pool = [{"id": "c1"}, {"id": "c2"}]
    with patch.object(waifu, "get_or_load_characters", AsyncMock(return_value=pool)):
        with patch.object(waifu, "_record_recent_reward", AsyncMock()) as record:
            assert await sample_character_by_rarity("⚪ Common") in pool
            record.assert_not_awaited()  # no user -> no history bookkeeping
