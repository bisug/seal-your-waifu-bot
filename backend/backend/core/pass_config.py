"""
Central Battle Pass configuration.

The pass is intentionally season-scoped. Legacy top-level fields are still
honored by helper functions so existing users keep their current entitlement
while new purchases are stored under pass_entitlements.<season_id>.
"""

CURRENT_PASS_SEASON = "s1"
PASS_SEASON_NAME = "Ascendant Tide"
MAX_PASS_LEVEL = 100
# Milestone levels with special (egg) rewards on the pass track.
PASS_MILESTONE_LEVELS = [5, 10, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100]
MID_PASS_MILESTONES = {25, 75}
HALFWAY_LEVEL = 50
FINAL_PASS_LEVEL = 100

PASS_TIERS = ("free", "premium", "elite")
PASS_TIER_RANK = {tier: rank for rank, tier in enumerate(PASS_TIERS)}

PASS_STAR_PRICES = {
    "premium": 24,
    "elite": 49,
}

PASS_TIER_META = {
    "free": {
        "name": "Free",
        "summary": "Base seasonal rewards",
    },
    "premium": {
        "name": "Premium",
        "summary": "Bank unlock, premium missions, better eggs, faster incubation",
    },
    "elite": {
        "name": "Elite",
        "summary": "All tracks, strongest economy, best egg luck, 3 incubators",
    },
}

PASS_BENEFITS = {
    "free": {
        "daily_multiplier": 1.0,
        "weekly_multiplier": 1.0,
        "hunt_multiplier": 1.0,
        "xp_multiplier": 1.0,
        "incubation_multiplier": 1.0,
        "egg_drop_multiplier": 1.0,
        "egg_quality_bonus": 0.0,
        "bonus_egg_chance": 0.0,
        "corruption_resistance": 0.0,
        "incubation_slots": 1,
        "mission_track": False,
    },
    "premium": {
        "daily_multiplier": 1.35,
        "weekly_multiplier": 1.35,
        "hunt_multiplier": 1.35,
        "xp_multiplier": 1.25,
        "incubation_multiplier": 0.65,
        "egg_drop_multiplier": 1.35,
        "egg_quality_bonus": 0.12,
        "bonus_egg_chance": 0.05,
        "corruption_resistance": 0.25,
        "incubation_slots": 2,
        "mission_track": True,
    },
    "elite": {
        "daily_multiplier": 1.75,
        "weekly_multiplier": 1.75,
        "hunt_multiplier": 1.75,
        "xp_multiplier": 1.50,
        "incubation_multiplier": 0.45,
        "egg_drop_multiplier": 1.75,
        "egg_quality_bonus": 0.28,
        "bonus_egg_chance": 0.12,
        "corruption_resistance": 0.50,
        "incubation_slots": 3,
        "mission_track": True,
    },
}

EGG_TIER_NAMES = {
    1: "gold",
    2: "void",
    3: "rare",
    4: "legendary",
    5: "celestial",
}


def normalize_pass_tier(tier: str | None) -> str:
    tier = str(tier or "free").lower()
    return tier if tier in PASS_TIER_RANK else "free"


def get_pass_rank(tier: str | None) -> int:
    """Numeric rank of a tier (free=0 < premium=1 < elite=2) for comparisons."""
    return PASS_TIER_RANK[normalize_pass_tier(tier)]


def get_active_pass_type(user: dict | None) -> str:
    """Resolve the user's effective pass tier for the current season (legacy-aware)."""
    if not user:
        return "free"

    entitlements = user.get("pass_entitlements") or {}
    season_entitlement = entitlements.get(CURRENT_PASS_SEASON) or {}
    season_tier = season_entitlement.get("tier")
    if season_tier:
        return normalize_pass_tier(season_tier)

    # Legacy compatibility. Existing users with pass_type keep it for s1.
    return normalize_pass_tier(user.get("pass_type", "free"))


def get_pass_claims_field() -> str:
    return f"pass_claims.{CURRENT_PASS_SEASON}"


def get_pass_bank_field() -> str:
    return f"pass_bank_by_season.{CURRENT_PASS_SEASON}"


def get_pass_claimed_levels(user: dict | None) -> list[int]:
    if not user:
        return []
    claims_by_season = user.get("pass_claims") or {}
    season_claims = claims_by_season.get(CURRENT_PASS_SEASON)
    if isinstance(season_claims, list):
        return season_claims
    return user.get("claimed_levels", [])


def get_pass_bank(user: dict | None) -> dict:
    if not user:
        return {"shards": 0}
    banks_by_season = user.get("pass_bank_by_season") or {}
    season_bank = banks_by_season.get(CURRENT_PASS_SEASON)
    if isinstance(season_bank, dict):
        return season_bank
    return user.get("pass_bank", {"shards": 0})


def calculate_pass_upgrade_price(current_tier: str | None, target_tier: str) -> int | None:
    """Stars price to upgrade between tiers (credit for the current one), or None if not an upgrade."""
    current_tier = normalize_pass_tier(current_tier)
    target_tier = normalize_pass_tier(target_tier)
    if target_tier == "free":
        return None
    if get_pass_rank(current_tier) >= get_pass_rank(target_tier):
        return None

    current_value = PASS_STAR_PRICES.get(current_tier, 0)
    target_value = PASS_STAR_PRICES[target_tier]
    return max(1, target_value - current_value)


def apply_pass_incubation_bonus(minutes: int, user: dict | None) -> int:
    """Scale egg incubation minutes by the user's tier multiplier (lower is faster)."""
    tier = get_active_pass_type(user)
    multiplier = PASS_BENEFITS[tier]["incubation_multiplier"]
    return max(1, int(minutes * multiplier))


def get_pass_incubation_slots(user: dict | None) -> int:
    """Number of simultaneous egg incubators the user's tier allows."""
    tier = get_active_pass_type(user)
    return int(PASS_BENEFITS[tier].get("incubation_slots", 1))


def _shards(amount: int) -> dict:
    return {"type": "shards", "amount": int(amount)}


def _egg(tier: int) -> dict:
    return {"type": "egg", "tier": int(tier)}


def _default_track(level: int) -> dict:
    return {
        "free": _shards(150 + level * 12),
        "premium": _shards(450 + level * 28),
        "elite": _shards(850 + level * 45),
    }


def _milestone_track(level: int) -> dict:
    track = _default_track(level)

    if level % 5 == 0:
        track.update({
            "free": _shards(1_250 + level * 15),
            "premium": _egg(1),
            "elite": _egg(2),
            "premium_extra_amount": 750 + level * 20,
            "elite_extra_amount": 1_500 + level * 35,
        })

    if level % 10 == 0:
        track.update({
            "free": _egg(1),
            "premium": _egg(2),
            "elite": _egg(3),
            "premium_extra_amount": 2_000 + level * 40,
            "elite_extra_amount": 5_000 + level * 70,
        })

    if level in MID_PASS_MILESTONES:
        track.update({
            "free": _egg(2),
            "premium": _egg(3),
            "elite": _egg(4),
            "premium_extra_amount": 5_000 + level * 60,
            "elite_extra_amount": 15_000 + level * 120,
        })

    if level == HALFWAY_LEVEL:
        track.update({
            "free": _egg(3),
            "premium": _egg(4),
            "elite": _egg(5),
            "premium_extra_amount": 15_000,
            "elite_extra_amount": 40_000,
        })

    if level == FINAL_PASS_LEVEL:
        track.update({
            "free": _egg(4),
            "premium": _egg(5),
            "elite": _egg(5),
            "premium_extra_amount": 50_000,
            "elite_extra_amount": 100_000,
        })

    return track


PASS_TRACKS = {level: _milestone_track(level) for level in range(1, MAX_PASS_LEVEL + 1)}

PASS_MILESTONES = PASS_MILESTONE_LEVELS
