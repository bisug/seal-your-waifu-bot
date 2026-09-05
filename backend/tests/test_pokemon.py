"""Pokémon engine regression: catalog shape, ownership, active selection, XP.

Run: cd backend && uv run python -m pytest tests/test_pokemon.py -q
"""

import asyncio
from unittest.mock import AsyncMock, patch

import backend.core.pokemon as poke


class _UpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


PIKA_CATALOG = {
    "dex": 25,
    "name": "Pikachu",
    "types": ["electric"],
    "img": "https://example.com/pikachu.png",
    "base_stats": {"hp": 35, "atk": 55, "def": 40, "spatk": 50, "spdef": 50, "spd": 90},
    "base_total": 320,
    "sort_order": 25,
    "enabled": True,
}


def test_normalize_merges_catalog():
    out = poke.normalize_pokemon({"dex": 25, "level": 3, "xp": 40}, PIKA_CATALOG)
    assert out["name"] == "Pikachu"
    assert out["types"] == ["electric"]
    assert out["level"] == 3
    assert out["xp_needed"] == 3 * poke.XP_PER_LEVEL
    assert out["is_active"] is False


def test_normalize_without_catalog_falls_back():
    out = poke.normalize_pokemon({"dex": 999, "level": 1, "xp": 0}, None)
    assert out["name"] == "Pokemon #999"
    assert out["types"] == []


def test_find_pokemon_by_int_and_str():
    owned = [{"dex": 25, "level": 1, "xp": 0}]
    assert poke.find_pokemon(owned, 25) is owned[0]
    assert poke.find_pokemon(owned, "25") is owned[0]
    assert poke.find_pokemon(owned, 26) is None
    assert poke.find_pokemon(owned, "nope") is None


def test_grant_pokemon_atomic_guard_rejects_duplicate():
    """Duplicate dex must not be pushed — the $ne guard makes it a no-op."""
    with patch.object(poke, "user_collection") as uc, \
         patch.object(poke, "get_catalog_pokemon", new=AsyncMock(return_value=PIKA_CATALOG)):
        uc.update_one = AsyncMock(return_value=_UpdateResult(0, 0))
        ok = asyncio.run(poke.grant_pokemon(111, 25))
        assert ok is False
        filt = uc.update_one.call_args.args[0]
        assert filt["pokemon.dex"] == {"$ne": 25}


def test_grant_pokemon_pushes_new_entry():
    with patch.object(poke, "user_collection") as uc, \
         patch.object(poke, "get_catalog_pokemon", new=AsyncMock(return_value=PIKA_CATALOG)):
        uc.update_one = AsyncMock(return_value=_UpdateResult(1, 1))
        ok = asyncio.run(poke.grant_pokemon(111, 25, level=5))
        assert ok is True
        push = uc.update_one.call_args.args[1]["$push"]["pokemon"]
        assert push["dex"] == 25 and push["level"] == 5 and push["xp"] == 0


def test_set_active_requires_ownership():
    with patch.object(poke, "user_collection") as uc:
        uc.find_one = AsyncMock(return_value={"id": 111, "pokemon": [{"dex": 25}], "current_pokemon": None})
        uc.update_one = AsyncMock(return_value=_UpdateResult(1, 1))
        assert asyncio.run(poke.set_active_pokemon(111, 25)) is True
        # Not owned -> False, no write.
        assert asyncio.run(poke.set_active_pokemon(111, 26)) is False


def test_add_pokemon_xp_levels_up():
    """250 XP at level 2 (needs 200) -> level 3 with 50 carryover."""
    user_doc = {"id": 111, "pokemon": [{"dex": 25, "level": 2, "xp": 0}], "current_pokemon": 25}
    with patch.object(poke, "user_collection") as uc, \
         patch.object(poke, "get_catalog_pokemon", new=AsyncMock(return_value=PIKA_CATALOG)):
        uc.find_one = AsyncMock(return_value=user_doc)
        uc.update_one = AsyncMock(return_value=_UpdateResult(1, 1))
        level = asyncio.run(poke.add_pokemon_xp(111, 250))
        assert level == 3
        set_op = uc.update_one.call_args.args[1]["$set"]
        assert set_op["pokemon.$.level"] == 3
        assert set_op["pokemon.$.xp"] == 50


def test_battle_stats_scale_with_level():
    stats = poke.battle_stats(poke.normalize_pokemon(
        {"dex": 25, "level": 10, "xp": 0},
        {**PIKA_CATALOG, "base_stats": PIKA_CATALOG["base_stats"]},
    ))
    assert stats["name"] == "Pikachu"
    assert stats["hp"] == 35 + 10 * 5
    assert stats["atk"] == (55 + 50) // 2 + 10 * 2
    assert stats["spd"] == 90 + 10
    assert stats["max_hp"] == stats["hp"]
