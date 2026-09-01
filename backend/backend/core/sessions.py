"""Temporary multi-step bot sessions: Redis-first with Mongo fallback.

Session IDs are short-lived keys like 'trade:{id}' or 'battle:{chat_id}'.
Consumed atomically (get+delete) so callbacks cannot be replayed.
Note: This is separate from the WebApp auth tokens in webapp/auth.py.
"""
import asyncio
import json
from datetime import timedelta
from typing import Optional

from backend.core.cache import rdel, rget_json
from backend.core.logging import get_logger
from backend.core.utils import get_now_utc
from backend.database import r as _redis
from backend.database import sessions_collection

LOGGER = get_logger(__name__)

TTL_SESSION = 1800

__all__ = ["create_session", "get_session", "delete_session", "consume_session"]


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


async def _store_session_mongo(key: str, data: dict, ttl: int):
    await sessions_collection.update_one(
        {"_id": key},
        {
            "$set": {
                "data": data,
                "expires_at_dt": get_now_utc() + timedelta(seconds=ttl),
            }
        },
        upsert=True,
    )


async def create_session(
    session_id: str,
    data: dict,
    ttl: int = TTL_SESSION,
    *,
    expire_after: int | None = None,
):
    """Create a temporary session for multi-step bot flows."""
    if expire_after is not None:
        ttl = expire_after
    key = _session_key(session_id)
    redis_written = False
    if _redis:
        try:
            await asyncio.wait_for(
                _redis.setex(key, ttl, json.dumps(data, default=str)),
                timeout=3.0,
            )
            redis_written = True
        except Exception as e:
            LOGGER.warning(f"Redis session SET error [{key}], using Mongo fallback: {e}")
    try:
        await _store_session_mongo(key, data, ttl)
    except Exception as e:
        if redis_written:
            LOGGER.warning(f"Mongo session fallback write failed [{key}]; Redis session is active: {e}")
            return
        raise


async def get_session(session_id: str) -> Optional[dict]:
    key = _session_key(session_id)
    if _redis:
        data = await rget_json(key)
        if data is not None:
            return data
    doc = await sessions_collection.find_one({
        "_id": key,
        "$or": [
            {"expires_at_dt": {"$exists": False}},
            {"expires_at_dt": {"$gt": get_now_utc()}},
        ],
    })
    return doc.get("data") if doc else None


async def delete_session(session_id: str):
    key = _session_key(session_id)
    await rdel(key)
    await sessions_collection.delete_one({"_id": key})


async def consume_session(session_id: str) -> Optional[dict]:
    """Atomically fetch and delete a bot session so callbacks cannot be replayed."""
    key = _session_key(session_id)
    if _redis:
        try:
            raw = await asyncio.wait_for(_redis.getdel(key), timeout=3.0)
            if raw is not None:
                try:
                    await sessions_collection.delete_one({"_id": key})
                except Exception as e:
                    LOGGER.warning(f"Mongo session cleanup failed after Redis consume [{key}]: {e}")
                return json.loads(raw)
        except Exception as e:
            LOGGER.warning(f"Redis GETDEL error [{key}]: {e}")

    doc = await sessions_collection.find_one_and_delete({
        "_id": key,
        "$or": [
            {"expires_at_dt": {"$exists": False}},
            {"expires_at_dt": {"$gt": get_now_utc()}},
        ],
    })
    return doc.get("data") if doc else None
