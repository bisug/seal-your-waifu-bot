"""Regression tests for spawn variety: recent-spawn exclusion.

Guards the "same character spawned repeatedly" bug:
1. _pick_excluding never returns an id on the recent list (when avoidable).
2. Tiny pools fall back to the full list instead of failing.
3. Empty recent list behaves like plain random.choice.
"""
import random

from backend.core.spawns import _pick_excluding

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
