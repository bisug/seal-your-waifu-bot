from __future__ import annotations

from typing import Any

from config import config

OWNER_ROLE = "owner"
MODERATOR_ROLE = "moderator"
UPLOADER_ROLE = "uploader"

ROLE_ORDER = {
    UPLOADER_ROLE: 1,
    MODERATOR_ROLE: 2,
    OWNER_ROLE: 3,
}

ROLE_META = {
    OWNER_ROLE: {
        "label": "Owner",
        "tag": "OWNER",
        "symbol": "★",
        "can_upload": True,
        "can_edit_character": True,
        "upload_reward": {"balance": 1000, "zenith": 10},
        "perks": {
            "daily_bonus_percent": 10,
            "weekly_bonus_percent": 8,
            "weekly_xp_bonus_percent": 5,
            "shop_discount_percent": 5,
            "sell_bonus_percent": 5,
        },
    },
    MODERATOR_ROLE: {
        "label": "Moderator",
        "tag": "MOD",
        "symbol": "◆",
        "can_upload": True,
        "can_edit_character": True,
        "upload_reward": {"balance": 700, "zenith": 7},
        "perks": {
            "daily_bonus_percent": 7,
            "weekly_bonus_percent": 5,
            "weekly_xp_bonus_percent": 3,
            "shop_discount_percent": 3,
            "sell_bonus_percent": 3,
        },
    },
    UPLOADER_ROLE: {
        "label": "Uploader",
        "tag": "UP",
        "symbol": "▲",
        "can_upload": True,
        "can_edit_character": False,
        "upload_reward": {"balance": 500, "zenith": 5},
        "perks": {
            "daily_bonus_percent": 5,
            "weekly_bonus_percent": 3,
            "weekly_xp_bonus_percent": 2,
            "shop_discount_percent": 2,
            "sell_bonus_percent": 2,
        },
    },
}

DEFAULT_PERKS = {
    "daily_bonus_percent": 0,
    "weekly_bonus_percent": 0,
    "weekly_xp_bonus_percent": 0,
    "shop_discount_percent": 0,
    "sell_bonus_percent": 0,
}

MANAGED_ROLES = {MODERATOR_ROLE, UPLOADER_ROLE}


def normalize_role(role: Any) -> str | None:
    value = str(role or "").strip().lower()
    aliases = {
        "mod": MODERATOR_ROLE,
        "moderator": MODERATOR_ROLE,
        "sudo": MODERATOR_ROLE,
        "admin": MODERATOR_ROLE,
        "upload": UPLOADER_ROLE,
        "uploader": UPLOADER_ROLE,
    }
    return aliases.get(value)


def _coerce_user_id(user_id: int | str | None) -> int | None:
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def get_user_role(user_id: int | str | None) -> str | None:
    uid = _coerce_user_id(user_id)
    if uid is None:
        return None
    if uid == config.OWNER_ID:
        return OWNER_ROLE

    try:
        from backend import sudo_roles, sudo_users
    except Exception:
        sudo_roles = {}
        sudo_users = config.SUDO_USERS

    role = normalize_role(sudo_roles.get(uid))
    if role:
        return role
    if uid in sudo_users:
        return MODERATOR_ROLE
    return None


def has_role_at_least(user_id: int | str | None, minimum_role: str) -> bool:
    role = get_user_role(user_id)
    if not role:
        return False
    return ROLE_ORDER[role] >= ROLE_ORDER[minimum_role]


def moderator(user_id: int | str | None) -> bool:
    return has_role_at_least(user_id, MODERATOR_ROLE)


def can_upload(user_id: int | str | None) -> bool:
    role = get_user_role(user_id)
    return bool(role and ROLE_META[role]["can_upload"])


def can_edit_character(user_id: int | str | None) -> bool:
    return moderator(user_id)


def is_staff(user_id: int | str | None) -> bool:
    return get_user_role(user_id) is not None


def get_role_perks(user_id: int | str | None) -> dict[str, int]:
    role = get_user_role(user_id)
    if not role:
        return dict(DEFAULT_PERKS)
    return {**DEFAULT_PERKS, **ROLE_META[role].get("perks", {})}


def _percent_amount(amount: int, percent: int, *, min_base: int = 100) -> int:
    amount = max(0, int(amount or 0))
    percent = max(0, int(percent or 0))
    if not amount or not percent:
        return 0
    bonus = amount * percent // 100
    if bonus == 0 and amount >= min_base:
        return 1
    return bonus


def apply_role_bonus(
    user_id: int | str | None,
    amount: int,
    perk_key: str,
    *,
    min_base: int = 100,
) -> tuple[int, int]:
    bonus = _percent_amount(amount, int(get_role_perks(user_id).get(perk_key, 0)), min_base=min_base)
    return int(amount) + bonus, bonus


def apply_role_discount(
    user_id: int | str | None,
    amount: int,
    *,
    min_base: int = 20,
) -> tuple[int, int]:
    discount = _percent_amount(amount, int(get_role_perks(user_id).get("shop_discount_percent", 0)), min_base=min_base)
    discounted = max(1, int(amount) - discount)
    return discounted, int(amount) - discounted


def format_role_benefits(perks: dict | None) -> list[str]:
    perks = {**DEFAULT_PERKS, **(perks or {})}
    benefits = []
    if perks["daily_bonus_percent"]:
        benefits.append(f"+{perks['daily_bonus_percent']}% daily shards")
    if perks["weekly_bonus_percent"]:
        benefits.append(f"+{perks['weekly_bonus_percent']}% weekly shards")
    if perks["weekly_xp_bonus_percent"]:
        benefits.append(f"+{perks['weekly_xp_bonus_percent']}% weekly XP")
    if perks["shop_discount_percent"]:
        benefits.append(f"{perks['shop_discount_percent']}% shop discount")
    if perks["sell_bonus_percent"]:
        benefits.append(f"+{perks['sell_bonus_percent']}% sell value")
    return benefits


def get_role_payload(user_id: int | str | None) -> dict:
    role = get_user_role(user_id)
    if not role:
        return {
            "role": None,
            "role_label": None,
            "role_tag": None,
            "role_symbol": None,
            "is_staff": False,
            "can_upload": False,
            "can_edit_character": False,
            "upload_reward": None,
            "role_perks": dict(DEFAULT_PERKS),
            "role_benefits": [],
        }

    meta = ROLE_META[role]
    perks = get_role_perks(user_id)
    return {
        "role": role,
        "role_label": meta["label"],
        "role_tag": meta["tag"],
        "role_symbol": meta["symbol"],
        "is_staff": True,
        "can_upload": bool(meta["can_upload"]),
        "can_edit_character": bool(meta["can_edit_character"]),
        "upload_reward": dict(meta["upload_reward"]),
        "role_perks": perks,
        "role_benefits": format_role_benefits(perks),
    }


def format_upload_reward(reward: dict | None) -> str:
    if not reward:
        return ""
    parts = []
    balance = int(reward.get("balance") or 0)
    zenith = int(reward.get("zenith") or 0)
    if balance:
        parts.append(f"+{balance:,} Shards")
    if zenith:
        parts.append(f"+{zenith:,} Zenith")
    return " and ".join(parts)


async def grant_upload_reward(user_id: int | str | None, *, source: str = "upload") -> dict | None:
    uid = _coerce_user_id(user_id)
    role = get_user_role(uid)
    if uid is None or not role:
        return None

    reward = dict(ROLE_META[role]["upload_reward"])
    inc = {
        "upload_count": 1,
        f"role_upload_counts.{role}": 1,
        f"role_upload_counts.{source}": 1,
        "version": 1,
    }
    if reward.get("balance"):
        inc["balance"] = int(reward["balance"])
    if reward.get("zenith"):
        inc["zenith"] = int(reward["zenith"])

    from backend.core.utils import get_user_id_query
    from backend.database import user_collection

    result = await user_collection.update_one(get_user_id_query(uid), {"$inc": inc})
    if result.matched_count == 0:
        await user_collection.update_one(
            {"id": uid},
            {"$setOnInsert": {"id": uid}, "$inc": inc},
            upsert=True,
        )
    return {
        **reward,
        "role": role,
        "role_tag": ROLE_META[role]["tag"],
        "text": format_upload_reward(reward),
    }
