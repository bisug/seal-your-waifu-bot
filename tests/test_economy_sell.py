"""Regression tests for character liquidation (sell / recycle) economy rules.

Guards two historically broken behaviours:
1. High-tier duplicates used to fall back to the Common sell price
   (e.g. a Celestial sold for 50 Shards) because SELL_PRICES only
   covered 8 of 25 rarities.
2. /recycle used to credit Zenith using a shard-scale table, which
   made the Zenith sink trivially farmable. Recycle now reuses the
   same Shards table as /sell via get_sell_price().
"""
import pytest

from Grabber.modules.economy.sell import get_sell_price, normalize_sell_rarity

# Rarity strings exactly as stored in the DB (emoji-prefixed).
ALL_RARITIES = [
    "⚪ Common", "🟢 Medium", "🟣 Epic", "🟠 Rare", "🟡 Legendary",
    "💠 Cosmic", "🧬 Immortal", "💮 Exclusive", "🌌 Eternal",
    "🔮 Limited Edition", "🔮 Mystic", "🫧 Royal", "💎 Antique",
    "💎 Mythical", "🎐 Celestial", "✨ Divine", "🌠 Astral",
    "🎞️ AMV", "🪽 Prestige", "❄️ Winter", "☀️ Summer",
    "💖 Valentine", "🎃 Halloween", "💸 Luxury", "🎏 Limited",
]


def test_every_rarity_has_a_sell_price():
    # Regression: previously high tiers returned the Common default (50)
    # because SELL_PRICES only listed 8 rarities.
    for rarity in ALL_RARITIES:
        assert get_sell_price(rarity) > 0


def test_higher_tier_is_worth_more_than_common():
    common = get_sell_price("⚪ Common")
    celestial = get_sell_price("🎐 Celestial")
    assert celestial > common
    # Top tiers should be meaningfully above commons, not a rounding error.
    assert celestial >= common * 100


def test_unknown_rarity_falls_back_to_common():
    common_price = get_sell_price("⚪ Common")
    assert get_sell_price("🌀 Some Future Rarity") == common_price
    assert get_sell_price("") == common_price


def test_normalize_returns_known_key():
    assert normalize_sell_rarity("🎐 Celestial") == "Celestial"
    assert normalize_sell_rarity("⚪ Common") == "Common"
    # Short, unprefixed forms still normalize.
    assert normalize_sell_rarity("Royal") == "Royal"
