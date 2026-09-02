"""Regression tests for pet care and level-scaled hunt luck.

Guards:
1. get_pet_luck scales with level (levels actually matter for hunts) and
   applies the affection mood multiplier.
2. get_pet_luck never exceeds a sane ceiling even at max level + happy mood.
"""
from backend.core.pets import (
    MAX_AFFECTION,
    get_pet_luck,
    normalize_pet,
)


def make_pet(level: int = 1, affection: int = 50, luck: float = 0.10) -> dict:
    return normalize_pet({
        "petid": "blaze_fang",
        "level": level,
        "xp": 0,
        "affection": affection,
        "last_interacted": 0,  # no decay
    })


def test_luck_increases_with_level():
    low = get_pet_luck(make_pet(level=1))
    high = get_pet_luck(make_pet(level=10))
    assert high > low
    # +2% per level above 1: level 10 should add exactly 0.18 over base.
    assert abs(high - low - 0.18) < 1e-9


def test_luck_mood_multiplier_applies():
    neutral = get_pet_luck(make_pet(affection=50))
    happy = get_pet_luck(make_pet(affection=MAX_AFFECTION))
    sad = get_pet_luck(make_pet(affection=10))
    assert happy > neutral > sad


def test_luck_ceiling_at_max_level():
    maxed = get_pet_luck(make_pet(level=100, affection=MAX_AFFECTION))
    # base 0.10 * 1.2 (happy) + 0.50 (level cap) = 0.62
    assert maxed <= 0.10 * 1.2 + 0.50 + 1e-9


def test_luck_handles_missing_pet():
    assert get_pet_luck(None) == 0.08
    assert get_pet_luck({}) == 0.08
