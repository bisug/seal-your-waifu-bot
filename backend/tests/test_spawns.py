"""Guards for spawn-pipeline optimizations.

1. send_character must skip automatic spawns while a recent spawn is still
   unclaimed (previously a new spawn silently replaced the old character,
   making it uncatchable), but force=True (/cnow) must bypass the guard.
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



def test_milestones_survive_rarity_rename():
    # Milestones are keyed by rarity_id, so a rename must not orphan them.
    from backend.core import rarities as cr

    original_docs = cr.get_rarity_docs()
    try:
        cr._apply_docs([dict(d, name=d["name"] + " X") for d in original_docs])
        rebuilt = message_counter._build_milestones()
        assert len(rebuilt) == len(message_counter._MILESTONES)
        # Every rarity_id still resolves to a (renamed) label with its threshold.
        by_threshold = sorted(rebuilt, key=lambda p: -p[1])
        assert by_threshold[0][1] == 10000  # Astral keeps its threshold
    finally:
        cr._apply_docs(original_docs)


def test_milestones_are_db_backed():
    # Milestone thresholds must come from the rarities collection docs
    # (editable via /rarityset), not a hardcoded table in message_counter.
    from backend.core import rarities as cr

    original_docs = cr.get_rarity_docs()
    try:
        edited = [dict(d) for d in original_docs]
        for d in edited:
            if d["_id"] == 8:  # Royal
                d["milestone"] = 1234
            if d["_id"] == 25:  # Astral
                d["milestone"] = 0  # zero removes the rarity from milestones
        cr._apply_docs(edited)
        rebuilt = message_counter._build_milestones()
        thresholds = dict((label, t) for label, t in rebuilt)
        assert thresholds[cr.RARITY_MAP[8]] == 1234
        assert cr.RARITY_MAP[25] not in thresholds
    finally:
        cr._apply_docs(original_docs)


def test_rarity_id_of_lookups():
    # O(1) lookup paths: full label, bare name (case-insensitive), int id,
    # and misses return None instead of raising.
    from backend.core.rarities import rarity_id_of

    assert rarity_id_of("🫧 Royal") == 8
    assert rarity_id_of("royal") == 8
    assert rarity_id_of("ROYAL") == 8
    assert rarity_id_of(8) == 8
    assert rarity_id_of("No Such Rarity") is None
    assert rarity_id_of(None) is None
    assert rarity_id_of(999) is None


def test_weighted_pick_rejects_all_zero_pool():
    # random.choices raises on all-zero weights; weighted_pick must return None.
    from backend.core.rarities import weighted_pick

    assert weighted_pick({}) is None
    assert weighted_pick({"⚪ Common": 0, "🟢 Medium": 0}) is None
    assert weighted_pick({"⚪ Common": 1}) == "⚪ Common"
