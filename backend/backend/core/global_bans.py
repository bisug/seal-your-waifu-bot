import time
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.core.cache import rdel, rget_json, rset_json
from backend.core.utils import get_now_utc
from backend.database import global_group_bans_collection, global_user_bans_collection

CACHE_TTL = 60
DEFAULT_GBAN_DAYS = 30

_user_cache: dict[int, tuple[float, dict[str, Any] | None]] = {}
_group_cache: dict[int, tuple[float, dict[str, Any] | None]] = {}


def _normalize_id(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed or None


def _cache_get(cache: dict[int, tuple[float, dict[str, Any] | None]], key: int):
    entry = cache.get(key)
    if not entry:
        return False, None
    expires_at, value = entry
    if expires_at <= time.monotonic():
        cache.pop(key, None)
        return False, None
    return True, value


def _cache_set(cache: dict[int, tuple[float, dict[str, Any] | None]], key: int, value):
    cache[key] = (time.monotonic() + CACHE_TTL, value)


def _strip_mongo_id(doc: dict[str, Any] | None):
    if not doc:
        return None
    cleaned = dict(doc)
    cleaned.pop("_id", None)
    return cleaned


def _coerce_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _is_expired(doc: dict[str, Any] | None) -> bool:
    expires_at = _coerce_datetime(doc.get("expires_at_dt") if doc else None)
    return bool(expires_at and expires_at <= get_now_utc())


def _expiry_after_days(days: int = DEFAULT_GBAN_DAYS) -> datetime:
    return get_now_utc() + timedelta(days=days)


async def get_user_gban(user_id: int | str):
    uid = _normalize_id(user_id)
    if uid is None:
        return None

    found, cached = _cache_get(_user_cache, uid)
    if found:
        return cached

    cache_key = f"gban:user:{uid}"
    payload = await rget_json(cache_key)
    if isinstance(payload, dict):
        doc = payload.get("doc") if payload.get("banned") else None
        if _is_expired(doc):
            await global_user_bans_collection.delete_one({"user_id": uid})
            await invalidate_user_gban(uid)
            return None
        _cache_set(_user_cache, uid, doc)
        return doc

    doc = _strip_mongo_id(await global_user_bans_collection.find_one({"user_id": uid}))
    if _is_expired(doc):
        await global_user_bans_collection.delete_one({"user_id": uid})
        await invalidate_user_gban(uid)
        return None
    await rset_json(cache_key, {"banned": bool(doc), "doc": doc}, CACHE_TTL)
    _cache_set(_user_cache, uid, doc)
    return doc


async def get_group_gban(chat_id: int | str):
    cid = _normalize_id(chat_id)
    if cid is None:
        return None

    found, cached = _cache_get(_group_cache, cid)
    if found:
        return cached

    cache_key = f"gban:group:{cid}"
    payload = await rget_json(cache_key)
    if isinstance(payload, dict):
        doc = payload.get("doc") if payload.get("banned") else None
        if _is_expired(doc):
            await global_group_bans_collection.delete_one({"chat_id": cid})
            await invalidate_group_gban(cid)
            return None
        _cache_set(_group_cache, cid, doc)
        return doc

    doc = _strip_mongo_id(await global_group_bans_collection.find_one({"chat_id": cid}))
    if _is_expired(doc):
        await global_group_bans_collection.delete_one({"chat_id": cid})
        await invalidate_group_gban(cid)
        return None
    await rset_json(cache_key, {"banned": bool(doc), "doc": doc}, CACHE_TTL)
    _cache_set(_group_cache, cid, doc)
    return doc


async def invalidate_user_gban(user_id: int | str):
    uid = _normalize_id(user_id)
    if uid is None:
        return
    _user_cache.pop(uid, None)
    await rdel(f"gban:user:{uid}")


async def invalidate_group_gban(chat_id: int | str):
    cid = _normalize_id(chat_id)
    if cid is None:
        return
    _group_cache.pop(cid, None)
    await rdel(f"gban:group:{cid}")


async def add_user_gban(
    user_id: int,
    *,
    reason: str,
    banned_by: int,
    user_name: str | None = None,
    duration_days: int = DEFAULT_GBAN_DAYS,
):
    doc = {
        "user_id": user_id,
        "user_name": user_name,
        "reason": reason,
        "banned_by": banned_by,
        "created_at": get_now_utc(),
        "expires_at_dt": _expiry_after_days(duration_days),
    }
    await global_user_bans_collection.update_one(
        {"user_id": user_id},
        {"$set": doc},
        upsert=True,
    )
    await invalidate_user_gban(user_id)
    return doc


async def remove_user_gban(user_id: int) -> bool:
    result = await global_user_bans_collection.delete_one({"user_id": user_id})
    await invalidate_user_gban(user_id)
    return result.deleted_count > 0


async def add_group_gban(
    chat_id: int,
    *,
    reason: str,
    banned_by: int,
    chat_title: str | None = None,
    duration_days: int = DEFAULT_GBAN_DAYS,
):
    doc = {
        "chat_id": chat_id,
        "chat_title": chat_title,
        "reason": reason,
        "banned_by": banned_by,
        "created_at": get_now_utc(),
        "expires_at_dt": _expiry_after_days(duration_days),
    }
    await global_group_bans_collection.update_one(
        {"chat_id": chat_id},
        {"$set": doc},
        upsert=True,
    )
    await invalidate_group_gban(chat_id)
    return doc


async def remove_group_gban(chat_id: int) -> bool:
    result = await global_group_bans_collection.delete_one({"chat_id": chat_id})
    await invalidate_group_gban(chat_id)
    return result.deleted_count > 0
