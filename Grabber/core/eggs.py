from Grabber.core.constants import EGG_TIERS
from Grabber.core.pets import get_caregiver_incubation_minutes


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
