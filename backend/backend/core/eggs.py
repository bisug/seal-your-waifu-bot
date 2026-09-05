import random

from backend.core.constants import EGG_TIERS

EGG_TIER_ORDER = ("common", "gold", "void", "rare", "legendary", "celestial")

# Liquidation value per egg tier (Coins). Scaled to the tier's rarity chance
# and incubation cost; deliberately below the fusion upgrade path so selling
# is the "I don't want to wait" option, not the optimal one.
EGG_SELL_PRICES = {
    "common": 50,
    "gold": 200,
    "void": 800,
    "rare": 2500,
    "legendary": 8000,
    "celestial": 25000,
}

# Cost to purify a corrupted egg (Coins), tier-scaled. Cheaper than losing
# the egg to a 30% explosion at hatch time.
EGG_PURIFY_PRICES = {
    "common": 500,
    "gold": 1000,
    "void": 2000,
    "rare": 3000,
    "legendary": 4000,
    "celestial": 5000,
}

TIER_MAP = {
    "1": "gold",
    "2": "void",
    "3": "rare",
    "4": "legendary",
    "5": "celestial",
}


def normalize_egg_tier(raw_tier) -> str:
    tier = str(raw_tier or "common").lower()
    tier = TIER_MAP.get(tier, tier)
    return tier if tier in EGG_TIERS else "common"


def get_egg_tier_info(raw_tier) -> tuple[str, dict]:
    """Normalized tier name plus its metadata dict."""
    tier = normalize_egg_tier(raw_tier)
    return tier, EGG_TIERS[tier]


def get_incubation_wait_minutes(raw_tier) -> int:
    """Incubation minutes for a tier."""
    _, tier_info = get_egg_tier_info(raw_tier)
    return tier_info["wait_min"]


def roll_egg_tier(luck_multiplier: float = 0.0, quality_bonus: float = 0.0) -> str:
    """Roll an egg tier using base tier weights and pass quality bonus."""
    luck_multiplier = max(0.0, float(luck_multiplier or 0.0))
    quality_bonus = max(0.0, float(quality_bonus or 0.0))

    weights = []
    for idx, tier in enumerate(EGG_TIER_ORDER):
        tier_info = EGG_TIERS[tier]
        base = float(tier_info.get("chance", 0.0))
        if tier == "common":
            weight = base * max(0.30, 1.0 - quality_bonus)
        else:
            luck_boost = 1.0 + luck_multiplier + (quality_bonus * (idx + 1))
            weight = base * luck_boost
        weights.append(max(0.0, weight))

    if not any(weights):
        return "common"
    return random.choices(EGG_TIER_ORDER, weights=weights, k=1)[0]


def get_incubating_count(eggs: list) -> int:
    """Count of eggs in the user's list currently incubating."""
    return sum(1 for egg in eggs if isinstance(egg, dict) and egg.get("status") == "incubating")


def get_egg_sell_price(raw_tier) -> int:
    """Shard value of an egg on the market."""
    tier, _ = get_egg_tier_info(raw_tier)
    return EGG_SELL_PRICES[tier]


def get_egg_purify_price(raw_tier) -> int:
    """Shard cost to cleanse a corrupted egg."""
    tier, _ = get_egg_tier_info(raw_tier)
    return EGG_PURIFY_PRICES[tier]


def get_next_egg_tier(raw_tier) -> str | None:
    """Tier above the given one, or None at the ceiling (celestial)."""
    tier, _ = get_egg_tier_info(raw_tier)
    idx = EGG_TIER_ORDER.index(tier)
    if idx + 1 >= len(EGG_TIER_ORDER):
        return None
    return EGG_TIER_ORDER[idx + 1]
