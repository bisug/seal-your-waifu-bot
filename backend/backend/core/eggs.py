import random

from backend.core.constants import EGG_TIERS
from backend.core.pets import get_caregiver_incubation_minutes


EGG_TIER_ORDER = ("common", "gold", "void", "rare", "legendary", "celestial")

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
    tier = normalize_egg_tier(raw_tier)
    return tier, EGG_TIERS[tier]


def get_incubation_wait_minutes(raw_tier, active_pet: dict | None = None) -> int:
    _, tier_info = get_egg_tier_info(raw_tier)
    return get_caregiver_incubation_minutes(tier_info["wait_min"], active_pet)


def roll_egg_tier(luck_multiplier: float = 0.0, quality_bonus: float = 0.0) -> str:
    """Roll an egg tier using base tier weights, pet luck, and pass quality bonus."""
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
    return sum(1 for egg in eggs if isinstance(egg, dict) and egg.get("status") == "incubating")
