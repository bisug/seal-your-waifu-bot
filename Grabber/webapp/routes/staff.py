from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from config import config
from Grabber.core.progression import get_level_from_xp
from Grabber.core.roles import (
    MODERATOR_ROLE,
    OWNER_ROLE,
    ROLE_META,
    ROLE_ORDER,
    format_role_benefits,
    normalize_role,
)
from Grabber.core.utils import normalize_user_id
from Grabber.database import collection, pet_catalog_collection, sudo_collection, user_collection
from Grabber.webapp.auth import require_sudo_user

router = APIRouter()

UPLOAD_SOURCE_KEYS = ("web_character", "bot_character", "web_pet", "bot_pet")
UPLOAD_DETAIL_LIMIT = 50


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _iso_datetime(value: Any) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return None


async def _get_sudo_records() -> list[dict[str, Any]]:
    records: dict[int, dict[str, Any]] = {
        int(config.OWNER_ID): {
            "user_id": int(config.OWNER_ID),
            "role": OWNER_ROLE,
            "source": "owner",
            "is_owner": True,
        }
    }

    for raw_id in getattr(config, "SUDO_USERS", []) or []:
        user_id = _safe_int(raw_id)
        if not user_id or user_id == config.OWNER_ID:
            continue
        records[user_id] = {
            "user_id": user_id,
            "role": MODERATOR_ROLE,
            "source": "config",
            "is_owner": False,
        }

    db_sudos = await sudo_collection.find({}).to_list(length=None)
    for sudo in db_sudos:
        user_id = _safe_int(sudo.get("user_id"))
        if not user_id or user_id == config.OWNER_ID:
            continue
        role = normalize_role(sudo.get("role")) or MODERATOR_ROLE
        records[user_id] = {
            "user_id": user_id,
            "role": role,
            "source": "database",
            "is_owner": False,
        }

    return sorted(
        records.values(),
        key=lambda item: (-ROLE_ORDER[item["role"]], item["user_id"]),
    )


async def _load_user_docs(user_ids: list[int]) -> dict[int, dict[str, Any]]:
    lookup_ids: list[int | str] = []
    for user_id in user_ids:
        lookup_ids.extend([user_id, str(user_id)])

    projection = {
        "_id": 0,
        "id": 1,
        "first_name": 1,
        "last_name": 1,
        "username": 1,
        "avatar": 1,
        "balance": 1,
        "zenith": 1,
        "xp": 1,
        "upload_count": 1,
        "role_upload_counts": 1,
        "created_at": 1,
    }
    docs = await user_collection.find({"id": {"$in": lookup_ids}}, projection).to_list(length=None)
    return {
        normalize_user_id(doc.get("id")): doc
        for doc in docs
        if normalize_user_id(doc.get("id"))
    }


def _display_name(user_id: int, user_doc: dict[str, Any] | None) -> str:
    if not user_doc:
        return f"User {str(user_id)[-4:]}"
    first_name = str(user_doc.get("first_name") or "").strip()
    last_name = str(user_doc.get("last_name") or "").strip()
    full_name = f"{first_name} {last_name}".strip()
    if full_name and full_name.lower() != "user":
        return full_name
    username = str(user_doc.get("username") or "").strip()
    return username or f"User {str(user_id)[-4:]}"


def _source_counts(user_doc: dict[str, Any] | None) -> dict[str, int]:
    raw_counts = (user_doc or {}).get("role_upload_counts") or {}
    return {key: _safe_int(raw_counts.get(key)) for key in UPLOAD_SOURCE_KEYS}


def _character_upload_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "character",
        "id": item.get("id"),
        "name": item.get("name") or "Unknown Character",
        "subtitle": item.get("anime") or item.get("rarity") or "Character",
        "rarity": item.get("rarity"),
        "image": item.get("img_url"),
        "uploaded_at": _iso_datetime(item.get("uploaded_at")),
    }


def _pet_upload_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "pet",
        "id": item.get("petid") or item.get("id"),
        "name": item.get("name") or "Unknown Pet",
        "subtitle": item.get("ability") or item.get("rarity") or "Pet",
        "rarity": item.get("rarity"),
        "image": item.get("img"),
        "uploaded_at": _iso_datetime(item.get("updated_at") or item.get("created_at")),
        "enabled": bool(item.get("enabled", True)),
    }


async def _get_uploads(user_id: int) -> tuple[int, int, list[dict[str, Any]], list[dict[str, Any]]]:
    id_values = [user_id, str(user_id)]
    character_filter = {"added_by_id": {"$in": id_values}}
    pet_filter = {"uploaded_by": {"$in": id_values}}

    character_count = await collection.count_documents(character_filter)
    pet_count = await pet_catalog_collection.count_documents(pet_filter)

    characters = await collection.find(
        character_filter,
        {"_id": 0, "id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1, "uploaded_at": 1},
    ).sort([("uploaded_at", -1), ("id", -1)]).to_list(length=UPLOAD_DETAIL_LIMIT)

    pets = await pet_catalog_collection.find(
        pet_filter,
        {
            "_id": 0,
            "petid": 1,
            "id": 1,
            "name": 1,
            "rarity": 1,
            "ability": 1,
            "img": 1,
            "enabled": 1,
            "updated_at": 1,
            "created_at": 1,
        },
    ).sort([("updated_at", -1), ("created_at", -1)]).to_list(length=UPLOAD_DETAIL_LIMIT)

    return (
        character_count,
        pet_count,
        [_character_upload_item(item) for item in characters],
        [_pet_upload_item(item) for item in pets],
    )


@router.get("/admin/sudos/contributions")
async def get_sudo_contributions(user_id: int = Depends(require_sudo_user)):
    records = await _get_sudo_records()
    user_docs = await _load_user_docs([record["user_id"] for record in records])

    staff = []
    summary = {
        "total_staff": len(records),
        "total_uploads": 0,
        "character_uploads": 0,
        "pet_uploads": 0,
        "persisted_character_uploads": 0,
        "persisted_pet_uploads": 0,
    }

    for record in records:
        target_id = record["user_id"]
        role = record["role"]
        meta = ROLE_META[role]
        user_doc = user_docs.get(target_id) or {}
        source_counts = _source_counts(user_doc)
        character_source_count = source_counts["web_character"] + source_counts["bot_character"]
        pet_source_count = source_counts["web_pet"] + source_counts["bot_pet"]
        persisted_character_count, persisted_pet_count, character_uploads_list, pet_uploads_list = await _get_uploads(target_id)

        character_uploads = max(character_source_count, persisted_character_count)
        pet_uploads = max(pet_source_count, persisted_pet_count)
        total_uploads = max(_safe_int(user_doc.get("upload_count")), character_uploads + pet_uploads)

        summary["total_uploads"] += total_uploads
        summary["character_uploads"] += character_uploads
        summary["pet_uploads"] += pet_uploads
        summary["persisted_character_uploads"] += persisted_character_count
        summary["persisted_pet_uploads"] += persisted_pet_count

        staff.append({
            "id": target_id,
            "first_name": user_doc.get("first_name") or _display_name(target_id, user_doc),
            "display_name": _display_name(target_id, user_doc),
            "username": user_doc.get("username"),
            "avatar": user_doc.get("avatar"),
            "role": role,
            "role_label": meta["label"],
            "role_tag": meta["tag"],
            "role_symbol": meta["symbol"],
            "role_source": record["source"],
            "is_owner": bool(record.get("is_owner")),
            "can_upload": bool(meta["can_upload"]),
            "can_edit_character": bool(meta["can_edit_character"]),
            "upload_reward": dict(meta["upload_reward"]),
            "role_benefits": format_role_benefits(meta.get("perks")),
            "stats": {
                "balance": _safe_int(user_doc.get("balance")),
                "zenith": _safe_int(user_doc.get("zenith")),
                "xp": _safe_int(user_doc.get("xp")),
                "level": get_level_from_xp(_safe_int(user_doc.get("xp"))),
                "member_since": _iso_datetime(user_doc.get("created_at")),
            },
            "contributions": {
                "total_uploads": total_uploads,
                "character_uploads": character_uploads,
                "pet_uploads": pet_uploads,
                "persisted_character_uploads": persisted_character_count,
                "persisted_pet_uploads": persisted_pet_count,
                "sources": source_counts,
            },
            "uploads": {
                "characters": character_uploads_list,
                "pets": pet_uploads_list,
                "limit": UPLOAD_DETAIL_LIMIT,
                "truncated": (
                    persisted_character_count > len(character_uploads_list)
                    or persisted_pet_count > len(pet_uploads_list)
                ),
            },
            "recent_uploads": {
                "characters": character_uploads_list[:8],
                "pets": pet_uploads_list[:8],
            },
        })

    return {
        "viewer_id": user_id,
        "summary": summary,
        "staff": staff,
    }
