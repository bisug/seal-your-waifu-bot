import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import config
from Grabber.database import r, sessions_collection, user_collection

security = HTTPBearer()
LOGGER = logging.getLogger(__name__)
SESSION_TTL = 3600



def validate_init_data(init_data: str):
    """Validates data received from Telegram Web App."""
    if not init_data:
        return False
        
    try:
        vals = dict(parse_qsl(init_data, keep_blank_values=True))
        msg_hash = vals.pop('hash', None)
        if not msg_hash:
            return False
            
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(vals.items())])
        
        for token in [config.TOKEN, config.SUB_TOKEN]:
            if not token:
                continue
            secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
            h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
            
            if hmac.compare_digest(h, msg_hash):
                auth_date = int(vals.get('auth_date', 0))
                now = time.time()
                if auth_date > now + 300 or now - auth_date > 86400: # 24 hours expiry, 5m clock skew
                    return False
                return vals
    except Exception:
        LOGGER.exception("validate_init_data error")
    return False

# Enforce a strict max cap to prevent DDoS memory leak if Redis dies
_MAX_FALLBACK = 5000
_fallback_rate_limits = OrderedDict()


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _token_key(token: str) -> str:
    return f"auth_token:{_token_digest(token)}"


def _legacy_token_key(token: str) -> str:
    return f"auth_token:{token}"


async def _store_session_mongo(session_key: str, token_key: str, token_digest: str, user_id: int | str):
    expiry = time.time() + SESSION_TTL
    expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL)
    await sessions_collection.update_one(
        {"_id": session_key},
        {
            "$set": {"token_digest": token_digest, "expires_at": expiry, "expires_at_dt": expiry_dt},
            "$unset": {"token": ""},
        },
        upsert=True
    )
    await sessions_collection.update_one(
        {"_id": token_key},
        {"$set": {"user_id": str(user_id), "expires_at": expiry, "expires_at_dt": expiry_dt}},
        upsert=True
    )


async def get_user_id_from_token(token: str) -> str | None:
    """Resolve a WebApp auth token through Redis, falling back to MongoDB."""
    token_keys = [_token_key(token), _legacy_token_key(token)]
    if r:
        try:
            for token_key in token_keys:
                user_id = await asyncio.wait_for(r.get(token_key), timeout=3.0)
                if user_id:
                    return str(user_id)
        except Exception as e:
            LOGGER.warning(f"Redis auth token lookup failed, using Mongo fallback: {e}")

    token_doc = await sessions_collection.find_one({
        "_id": {"$in": token_keys},
        "$or": [
            {"expires_at": {"$gt": time.time()}},
            {"expires_at_dt": {"$gt": datetime.now(timezone.utc)}},
        ],
    })
    if not token_doc:
        return None
    return str(token_doc.get("user_id", "")).strip() or None

async def create_session(user_data: dict):
    """Creates a Redis session with MongoDB fallback."""
    user_id = user_data.get('id')
    if not user_id:
        user_json = json.loads(user_data.get('user', '{}'))
        user_id = user_json.get('id')
        
    if not user_id:
        return None
        
    token = str(uuid.uuid4())
    token_digest = _token_digest(token)
    session_key = f"user_session:{user_id}"
    token_key = _token_key(token)

    redis_written = False
    if r:
        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.setex(session_key, SESSION_TTL, token_digest)
                pipe.setex(token_key, SESSION_TTL, str(user_id))
                await asyncio.wait_for(pipe.execute(), timeout=3.0)
            redis_written = True
        except Exception as e:
            LOGGER.warning(f"Redis auth session write failed, using Mongo fallback: {e}")

    try:
        await _store_session_mongo(session_key, token_key, token_digest, user_id)
    except Exception:
        if redis_written:
            LOGGER.exception("Mongo auth session fallback write failed; Redis session is active")
        else:
            raise

    return token, user_id

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """Middleware to validate session and handle rate limiting."""
    token = auth.credentials
    user_id = await get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Rate Limiting: 30 req / 60s (sliding window)
    now = time.time()
    rate_key = f"rate_limit:{user_id}"

    if r:
        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(rate_key, 0, now - 60)
                pipe.zadd(rate_key, {str(now): now})
                pipe.zcard(rate_key)
                pipe.expire(rate_key, 60)
                _, _, count, _ = await asyncio.wait_for(pipe.execute(), timeout=3.0)

            if count > 30:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
            return int(user_id)
        except HTTPException:
            raise
        except Exception as e:
            LOGGER.warning(f"Redis rate limiting failed, using local fallback: {e}")

    # Enforce LRU cleanup to avoid memory leak if Redis falls over or is disabled.
    history = _fallback_rate_limits.get(user_id, [])
    history = [ts for ts in history if now - ts < 60]
    if len(history) >= 30:
        _fallback_rate_limits[user_id] = history
        _fallback_rate_limits.move_to_end(user_id)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    history.append(now)
    _fallback_rate_limits[user_id] = history
    _fallback_rate_limits.move_to_end(user_id)
    while len(_fallback_rate_limits) > _MAX_FALLBACK:
        _fallback_rate_limits.popitem(last=False)

    return int(user_id)


def is_sudo_user_id(user_id: int | str) -> bool:
    from Grabber.core.roles import can_edit_character

    return can_edit_character(user_id)


async def require_sudo_user(user_id: int = Depends(get_current_user)):
    if not is_sudo_user_id(user_id):
        raise HTTPException(status_code=403, detail="Moderator access required")
    return user_id


async def require_uploader_user(user_id: int = Depends(get_current_user)):
    from Grabber.core.roles import can_upload

    if not can_upload(user_id):
        raise HTTPException(status_code=403, detail="Uploader access required")
    return user_id

async def get_current_user_data(user_id: int = Depends(get_current_user)):
    """Dependency to fetch the full user document."""
    from Grabber.core.utils import get_user_id_query
    from Grabber.core.user import add_user_set_on_insert, get_user_filter
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        await user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert({}, user_id),
            upsert=True,
        )
        user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
