from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Grabber import LOGGER, user_collection
from Grabber.core.cache import invalidate_user_cache
from Grabber.core.pets import copy_default_pet, get_pet_key
from Grabber.core.progression import add_xp
from Grabber.core.user import get_user_filter, get_user_id
from Grabber.core.utils import get_now_utc
from Grabber.modules.progression.achievements import check_achievements

REFERRER_REWARD_SHARDS = 500
REFERRER_REWARD_XP = 50
REFERRED_REWARD_SHARDS = 1_500
REFERRED_PET_LEVEL = 10
MAX_REFERRAL_EVENTS = 100


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ReferralClaimResult:
    status: str
    referrer_id: int = 0
    referrer_reward_shards: int = REFERRER_REWARD_SHARDS
    referrer_reward_xp: int = REFERRER_REWARD_XP
    referred_reward_shards: int = REFERRED_REWARD_SHARDS
    referred_pet_level: int = REFERRED_PET_LEVEL

    @property
    def applied(self) -> bool:
        return self.status == "applied"


def parse_referral_payload(payload: str | None) -> int:
    if not payload or not payload.startswith("ref_"):
        return 0
    return get_user_id(payload.split("_", 1)[1])


def normalize_referral_ids(raw_referrals: Any) -> list[int]:
    if not isinstance(raw_referrals, list):
        return []

    seen: set[int] = set()
    referral_ids: list[int] = []
    for raw_id in raw_referrals:
        referred_id = get_user_id(raw_id)
        if referred_id <= 0 or referred_id in seen:
            continue
        seen.add(referred_id)
        referral_ids.append(referred_id)
    return referral_ids


def get_referral_stats(user: dict | None) -> dict[str, int]:
    if not user:
        return {
            "invited_count": 0,
            "tracked_count": 0,
            "earned_shards": 0,
            "referrer_reward_shards": REFERRER_REWARD_SHARDS,
            "referrer_reward_xp": REFERRER_REWARD_XP,
            "referred_reward_shards": REFERRED_REWARD_SHARDS,
            "referred_pet_level": REFERRED_PET_LEVEL,
        }

    tracked_count = len(normalize_referral_ids(user.get("referrals", [])))
    stored_count = max(_safe_int(user.get("referrals_count")), 0)
    invited_count = max(stored_count, tracked_count)
    earned_shards = _safe_int(user.get("referrals_earned"))
    if earned_shards <= 0 and invited_count:
        earned_shards = invited_count * REFERRER_REWARD_SHARDS

    return {
        "invited_count": invited_count,
        "tracked_count": tracked_count,
        "earned_shards": max(earned_shards, 0),
        "referrer_reward_shards": REFERRER_REWARD_SHARDS,
        "referrer_reward_xp": REFERRER_REWARD_XP,
        "referred_reward_shards": REFERRED_REWARD_SHARDS,
        "referred_pet_level": REFERRED_PET_LEVEL,
    }


async def claim_referral_bonus(
    *,
    user_id: Any,
    referrer_id: Any,
    is_new_user: bool,
    first_name: str | None = None,
    username: str | None = None,
) -> ReferralClaimResult:
    referred_id = get_user_id(user_id)
    normalized_referrer_id = get_user_id(referrer_id)

    if not is_new_user:
        return ReferralClaimResult("not_new_user", normalized_referrer_id)
    if referred_id <= 0 or normalized_referrer_id <= 0:
        return ReferralClaimResult("invalid_payload", normalized_referrer_id)
    if referred_id == normalized_referrer_id:
        return ReferralClaimResult("self_referral", normalized_referrer_id)

    referrer = await user_collection.find_one(
        get_user_filter(normalized_referrer_id),
        {"id": 1},
    )
    if not referrer:
        return ReferralClaimResult("missing_referrer", normalized_referrer_id)

    now = get_now_utc()
    upgraded_pet = copy_default_pet()
    upgraded_pet["level"] = REFERRED_PET_LEVEL

    claim_filter = get_user_filter(referred_id)
    claim_filter["referred_by"] = {"$exists": False}
    claim_result = await user_collection.update_one(
        claim_filter,
        {
            "$set": {
                "pets": [upgraded_pet],
                "current_pet": get_pet_key(upgraded_pet),
                "referred_by": normalized_referrer_id,
                "referral_reward": {
                    "shards": REFERRED_REWARD_SHARDS,
                    "pet_level": REFERRED_PET_LEVEL,
                },
                "referral_rewarded_at": now,
            },
            "$inc": {"balance": REFERRED_REWARD_SHARDS, "version": 1},
        },
        upsert=False,
    )
    if claim_result.modified_count == 0:
        return ReferralClaimResult("already_claimed", normalized_referrer_id)

    await invalidate_user_cache(referred_id)

    referral_event = {
        "user_id": referred_id,
        "first_name": first_name or "User",
        "username": username,
        "reward_shards": REFERRER_REWARD_SHARDS,
        "reward_xp": REFERRER_REWARD_XP,
        "created_at": now,
    }
    referrer_result = await user_collection.update_one(
        get_user_filter(normalized_referrer_id),
        {
            "$inc": {
                "balance": REFERRER_REWARD_SHARDS,
                "referrals_count": 1,
                "referrals_earned": REFERRER_REWARD_SHARDS,
                "version": 1,
            },
            "$addToSet": {"referrals": referred_id},
            "$push": {
                "referral_events": {
                    "$each": [referral_event],
                    "$slice": -MAX_REFERRAL_EVENTS,
                }
            },
        },
        upsert=False,
    )
    if referrer_result.matched_count == 0:
        LOGGER.warning(
            "Referral claim for %s accepted, but referrer %s disappeared before payout.",
            referred_id,
            normalized_referrer_id,
        )
        return ReferralClaimResult("missing_referrer_after_claim", normalized_referrer_id)

    await invalidate_user_cache(normalized_referrer_id)
    await add_xp(normalized_referrer_id, REFERRER_REWARD_XP, "referral")
    await check_achievements(normalized_referrer_id)
    return ReferralClaimResult("applied", normalized_referrer_id)
