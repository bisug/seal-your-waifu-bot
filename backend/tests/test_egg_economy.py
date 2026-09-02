"""Regression tests for the egg economy: sell prices, purify costs, fusion ladder.

Guards:
1. Every tier has a sell price and purify cost, strictly increasing with tier.
2. Fusion ladder is exhaustive: every tier below celestial upgrades, celestial
   is the ceiling.
3. Selling is never worth more than the fused upgrade path implies (sanity
   on the price ladder shape).
"""
from backend.core.constants import EGG_TIERS
from backend.core.eggs import (
    EGG_TIER_ORDER,
    EGG_PURIFY_PRICES,
    EGG_SELL_PRICES,
    get_egg_purify_price,
    get_egg_sell_price,
    get_next_egg_tier,
    normalize_egg_tier,
)


def test_every_tier_has_prices():
    for tier in EGG_TIER_ORDER:
        assert EGG_SELL_PRICES[tier] > 0
        assert EGG_PURIFY_PRICES[tier] > 0


def test_prices_increase_with_tier():
    for cheaper, pricier in zip(EGG_TIER_ORDER, EGG_TIER_ORDER[1:]):
        assert EGG_SELL_PRICES[pricier] > EGG_SELL_PRICES[cheaper]
        assert EGG_PURIFY_PRICES[pricier] >= EGG_PURIFY_PRICES[cheaper]


def test_price_helpers_normalize_legacy_tiers():
    # Legacy numeric tiers ("1".."5") and unknown values must resolve cleanly.
    assert get_egg_sell_price("1") == EGG_SELL_PRICES["gold"]
    assert get_egg_purify_price("bogus") == EGG_PURIFY_PRICES["common"]
    assert normalize_egg_tier(None) == "common"


def test_fusion_ladder_is_exhaustive():
    for tier in EGG_TIER_ORDER[:-1]:
        nxt = get_next_egg_tier(tier)
        assert nxt is not None
        assert EGG_TIERS[nxt]["rank"] == EGG_TIERS[tier]["rank"] + 1
    # Celestial is the ceiling.
    assert get_next_egg_tier("celestial") is None


def test_fusion_is_better_value_than_selling():
    # 3 fused commons should never sell for less than the 3 sold commons —
    # otherwise fusion is a trap and the ladder is mispriced.
    for tier in EGG_TIER_ORDER[:-1]:
        nxt = get_next_egg_tier(tier)
        assert EGG_SELL_PRICES[nxt] > EGG_SELL_PRICES[tier] * 3
