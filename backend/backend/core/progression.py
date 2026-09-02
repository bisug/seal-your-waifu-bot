import math

from backend.core.logging import get_logger
from backend.core.pass_config import (
    CURRENT_PASS_SEASON,
    MAX_PASS_LEVEL,
    PASS_TRACKS,
    get_active_pass_type,
    get_pass_bank_field,
    get_pass_claimed_levels,
    get_pass_claims_field,
    get_pass_rank,
)
from backend.core.user import add_user_set_on_insert, get_user_filter
from backend.database import user_collection

LOGGER = get_logger(__name__)
LEVEL_CAP = MAX_PASS_LEVEL
LEVEL_REWARDS = {
    5: {"free": 1000, "premium": 3000, "elite": 5000},
    10: {"free": "egg_common", "premium": "egg_gold", "elite": "egg_void"},
    25: {"free": 5000, "premium": 15000, "elite": 25000},
    50: {"free": 10000, "premium": 30000, "elite": 50000}
}
def get_level_from_xp(xp: int) -> int:
    """
    Calculate the current level based on total XP using the sum of arithmetic progression formula.
    XP required for level L = 50 * L * (L + 1).
    Inverse: L = (-1 + sqrt(1 + XP / 12.5)) / 2.
    """
    if xp <= 0:
        return 0
    # Quadratic formula to find level L
    level = int((-1 + math.sqrt(1 + xp / 12.5)) / 2)
    return min(level, LEVEL_CAP)
def get_xp_for_next_level(current_level: int) -> int:
    """
    Calculate the total XP required to reach the next level.
    """
    if current_level >= LEVEL_CAP:
        return 0
    return 100 * (current_level + 1)
def get_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Generate a visual progress bar string.
    """
    if total == 0:
        return "[" + "░" * length + "]"
    filled = int((current / total) * length)
    empty = length - filled
    return "[" + "█" * filled + "░" * empty + "]"
async def add_xp(
    user_id: int,
    amount: int,
    source: str = "unknown",
    *,
    session=None,
    sync_rank: bool = True,
):
    """
    Add XP to a user's profile and handle level-ups atomically.
    """
    user = await user_collection.find_one_and_update(
        get_user_filter(user_id),
        add_user_set_on_insert({
            "$inc": {"xp": amount, "version": 1},
            "$setOnInsert": {
                "pass_type": "free",
                "claimed_levels": [],
                "season": CURRENT_PASS_SEASON
            }
        }, user_id),
        upsert=True,
        return_document=True,
        session=session,
    )
    if not user:
        return
    new_xp = user.get("xp", 0)
    # Sync with Redis Ranking Cache
    if sync_rank:
        from backend.core.leaderboard import update_user_rank
        await update_user_rank(user_id, new_xp)
    old_xp = new_xp - amount
    old_level = get_level_from_xp(old_xp)
    new_level = get_level_from_xp(new_xp)
    LOGGER.info(f"User {user_id} gained {amount} XP from {source}. Level: {old_level} -> {new_level}")
    if new_level > old_level:
        await check_and_grant_rewards(user_id, old_level, new_level, user, session=session)
    return new_xp
def _fallback_level_reward(level: int, pass_type: str) -> int:
    """Scaling for levels beyond the defined PASS_TRACKS table."""
    if pass_type == "free":
        return 100 + (level * 2)
    if pass_type == "premium":
        return 300 + (level * 4)
    return 500 + (level * 6)


def _compute_pass_rewards(
    pass_type: str, old_level: int, new_level: int, claimed_levels: set
) -> tuple[list, int, list, int, dict]:
    """
    Compute rewards for levels in (old_level, new_level] not yet claimed.
    Returns (newly_claimed, coins_earned, eggs_awarded, bank_shards, bank_eggs).
    Unowned-tier rewards are banked instead of granted.
    """
    import uuid

    total_coins_earned = 0
    eggs_awarded = []
    newly_claimed = []  # Tracks only levels claimed in this call (for $addToSet)
    bank_shards = 0
    bank_eggs = {}  # tier: count

    def add_egg(tier):
        eggs_awarded.append({
            "id": str(uuid.uuid4()),
            "tier": str(tier),
            "status": "fresh"
        })

    def bank_egg(tier):
        tier_str = str(tier)
        bank_eggs[tier_str] = bank_eggs.get(tier_str, 0) + 1

    def apply_reward(reward: dict, extra_amount: int = 0, *, bank: bool = False):
        nonlocal total_coins_earned, bank_shards
        if reward["type"] == "shards":
            if bank:
                bank_shards += reward["amount"]
            else:
                total_coins_earned += reward["amount"]
        elif reward["type"] == "egg":
            if bank:
                bank_egg(reward["tier"])
            else:
                add_egg(reward["tier"])
        if extra_amount:
            if bank:
                bank_shards += extra_amount
            else:
                total_coins_earned += extra_amount

    for level in range(old_level + 1, new_level + 1):
        if level in claimed_levels:
            continue
        # Track *newly* claimed levels separately so we can use $addToSet
        # instead of the old $set which overwrote the whole array. Two concurrent
        # reward grants (e.g. rapid XP from two sources) both fetching the same
        # stale claimed_levels and writing back would silently erase each other's
        # additions. $addToSet is atomic — MongoDB handles deduplication server-side.
        newly_claimed.append(level)
        claimed_levels.add(level)
        track = PASS_TRACKS.get(level)
        if not track:
            # Fallback scaling for level > 100
            total_coins_earned += _fallback_level_reward(level, pass_type)
            continue

        apply_reward(track["free"])

        premium_extra = track.get("premium_extra_amount", 0)
        if get_pass_rank(pass_type) >= get_pass_rank("premium"):
            apply_reward(track["premium"], premium_extra)
        else:
            apply_reward(track["premium"], premium_extra, bank=True)

        elite_extra = track.get("elite_extra_amount", 0)
        if pass_type == "elite":
            apply_reward(track["elite"], elite_extra)
        else:
            apply_reward(track["elite"], elite_extra, bank=True)

    return newly_claimed, total_coins_earned, eggs_awarded, bank_shards, bank_eggs


async def check_and_grant_rewards(user_id: int, old_level: int, new_level: int, user_data: dict = None, *, session=None):
    """
    Iterate through newly reached levels and grant corresponding rewards
    based on the user's Battle Pass type. Also tracks Pass Bank for free users.
    """
    if user_data is None:
        user = await user_collection.find_one(get_user_filter(user_id), session=session)
    else:
        user = user_data
    pass_type = get_active_pass_type(user)
    claimed_levels = set(get_pass_claimed_levels(user))
    newly_claimed, total_coins_earned, eggs_awarded, bank_shards, bank_eggs = _compute_pass_rewards(
        pass_type, old_level, new_level, claimed_levels
    )
    # Perform DB Updates
    updates = {}
    # Use $addToSet instead of $set so concurrent grants don't overwrite each other
    if newly_claimed:
        updates["$addToSet"] = {
            get_pass_claims_field(): {"$each": newly_claimed},
            "claimed_levels": {"$each": newly_claimed},
        }
    if total_coins_earned > 0:
        updates.setdefault("$inc", {})["balance"] = total_coins_earned
    if bank_shards > 0:
        updates.setdefault("$inc", {})[f"{get_pass_bank_field()}.shards"] = bank_shards
    for tier, count in bank_eggs.items():
        updates.setdefault("$inc", {})[f"{get_pass_bank_field()}.eggs_t{tier}"] = count
    if eggs_awarded:
        updates["$push"] = {"eggs": {"$each": eggs_awarded}}
    if updates.get("$inc") or updates.get("$push") or updates.get("$addToSet"):
        await user_collection.update_one(
            get_user_filter(user_id),
            updates,
            session=session,
        )
        if total_coins_earned > 0 or eggs_awarded:
            LOGGER.info(f"User {user_id} pass rewards: {total_coins_earned} shards, {len(eggs_awarded)} eggs")
async def get_user_progress(user_id: int, user_data: dict = None) -> dict:
    """
    Retrieve a comprehensive summary of a user's progression state.
    Supports lazy loading by passing existing user_data to avoid DB lookup.
    """
    if user_data is None:
        user = await user_collection.find_one(get_user_filter(user_id))
    else:
        user = user_data
    if not user:
        return {
            "level": 0,
            "xp": 0,
            "xp_current": 0,
            "xp_needed": 100,
            "pass_type": "free",
            "season": CURRENT_PASS_SEASON,
            "claimed_levels": []
        }
    total_xp = user.get("xp", 0)
    level = get_level_from_xp(total_xp)
    xp_needed = get_xp_for_next_level(level)
    # Optimized formula for sum of arithmetic progression: 100 * (1 + 2 + ... + n) = 50 * n * (n + 1)
    xp_for_previous_levels = 50 * level * (level + 1)
    xp_current = 0 if xp_needed == 0 else total_xp - xp_for_previous_levels
    return {
        "level": level,
        "xp": total_xp,
        "xp_current": xp_current,
        "xp_needed": xp_needed,
        "pass_type": get_active_pass_type(user),
        "season": user.get("season", CURRENT_PASS_SEASON),
        "claimed_levels": get_pass_claimed_levels(user)
    }
