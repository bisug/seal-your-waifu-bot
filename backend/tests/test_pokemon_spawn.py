"""Guess-the-Pokémon spawn regression: state round-trip, claim, name matching.

Run: cd backend && uv run python -m pytest tests/test_pokemon_spawn.py -q
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import backend.core.spawns as spawns
from backend.modules.collection.pokemon_guess import _name_variants


class _UpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


def test_name_variants_full_and_parts():
    assert "pikachu" in _name_variants("Pikachu")
    assert "mr" not in _name_variants("Mr Mime")  # short part excluded
    assert "mime" in _name_variants("Mr Mime")
    assert "mr mime" in _name_variants("Mr Mime")


def test_name_variants_case_and_space_normalized():
    assert _name_variants("  PIKACHU ") == {"pikachu"}


def test_clear_active_pokemon_spawn_claims_once():
    """Atomic Mongo claim: first caller True, second (0 modified) False."""
    with patch.object(spawns, "spawns_collection") as sc, \
         patch.object(spawns, "_redis", None):
        sc.update_one = AsyncMock(return_value=_UpdateResult(1, 1))
        assert asyncio.run(spawns.clear_active_pokemon_spawn(-100, 42)) is True
        sc.update_one = AsyncMock(return_value=_UpdateResult(1, 0))
        assert asyncio.run(spawns.clear_active_pokemon_spawn(-100, 43)) is False
        filt = sc.update_one.call_args.args[0]
        assert filt["_id"] == "pokespawn:-100"
        assert filt["pokemon"] == {"$ne": None}


def test_get_active_pokemon_spawn_redis_roundtrip():
    """Redis hash values decode to typed {dex, name, message_id}."""
    raw = {b"dex": b"25", b"name": b"Pikachu", b"message_id": b"777"}
    redis = MagicMock()
    redis.hgetall = AsyncMock(return_value=raw)
    with patch.object(spawns, "_redis", redis), \
         patch.object(spawns, "spawns_collection") as sc:
        sc.find_one = AsyncMock(return_value=None)
        out = asyncio.run(spawns.get_active_pokemon_spawn(-100))
        assert out == {"dex": 25, "name": "Pikachu", "message_id": 777}


def test_get_active_pokemon_spawn_mongo_fallback():
    """No Redis state -> Mongo doc keyed on the dedicated pokespawn _id."""
    doc = {
        "_id": "pokespawn:-100",
        "pokemon": {"dex": 133, "name": "Eevee"},
        "message_id": 555,
        "last_spawn_time": spawns.time.time(),
    }
    with patch.object(spawns, "_redis", None), \
         patch.object(spawns, "spawns_collection") as sc:
        sc.find_one = AsyncMock(return_value=doc)
        out = asyncio.run(spawns.get_active_pokemon_spawn(-100))
        assert out == {"dex": 133, "name": "Eevee", "message_id": 555}
        filt = sc.find_one.call_args.args[0]
        assert filt["_id"] == "pokespawn:-100"


def test_stale_pokemon_spawn_reads_as_gone():
    """Unguessed spawn older than MAX_AGE must not block the next one."""
    doc = {
        "_id": "pokespawn:-100",
        "pokemon": {"dex": 133, "name": "Eevee"},
        "message_id": 555,
        "last_spawn_time": spawns.time.time() - spawns.POKEMON_SPAWN_MAX_AGE_SECONDS - 10,
    }
    with patch.object(spawns, "_redis", None), \
         patch.object(spawns, "spawns_collection") as sc:
        sc.find_one = AsyncMock(return_value=None)  # TTL filter excludes it
        assert asyncio.run(spawns.get_active_pokemon_spawn(-100)) is None
        filt = sc.find_one.call_args.args[0]
        assert "last_spawn_time" in filt  # age filter present


def test_pokemon_slot_counter_redis():
    """Slot counter: every Nth spawn slot is the Pokémon one."""
    calls = []

    class _Pipe:
        def incr(self, key):
            calls.append(key)
            return self

        def expire(self, key, ttl):
            return self

        async def execute(self):
            return [len(calls), None]

    class _PipeCtx:
        async def __aenter__(self):
            return _Pipe()

        async def __aexit__(self, *exc):
            return False

    redis = MagicMock()
    redis.pipeline = MagicMock(return_value=_PipeCtx())
    with patch.object(spawns, "_redis", redis):
        results = [asyncio.run(spawns._next_pokemon_spawn_slot(-100))
                   for _ in range(spawns.POKEMON_SPAWN_EVERY)]
    assert results[-1] is True  # Nth slot fires
    assert not any(results[:-1])  # earlier slots don't


def test_pokemon_slot_counter_no_redis_fallback():
    """Redis-less mode: in-process counter still cycles 1-in-N."""
    with patch.object(spawns, "_redis", None):
        spawns._pokemon_slot_counter.clear()
        results = [asyncio.run(spawns._next_pokemon_spawn_slot(-100))
                   for _ in range(spawns.POKEMON_SPAWN_EVERY)]
    assert results[-1] is True
    assert not any(results[:-1])


def test_get_active_pokemon_spawn_none_when_empty():
    with patch.object(spawns, "_redis", None), \
         patch.object(spawns, "spawns_collection") as sc:
        sc.find_one = AsyncMock(return_value=None)
        assert asyncio.run(spawns.get_active_pokemon_spawn(-100)) is None
