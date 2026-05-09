import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from collections import OrderedDict, defaultdict
from typing import Dict
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import config
from Grabber.database import r, sessions_collection, user_collection

security = HTTPBearer()



def validate_init_data(init_data: str):
    """Validates data received from Telegram Web App."""
    if not init_data:
        return False
        
    try:
        vals = dict(parse_qsl(init_data))
        msg_hash = vals.pop('hash', None)
        if not msg_hash:
            return False
            
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(vals.items())])
        
        secret_key = hmac.new(b"WebAppData", config.TOKEN.encode(), hashlib.sha256).digest()
        h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(h, msg_hash):
            auth_date = int(vals.get('auth_date', 0))
            if time.time() - auth_date > 86400: # 24 hours expiry
                return False
            return vals
    except Exception:
        pass
    return False

# Enforce a strict max cap to prevent DDoS memory leak if Redis dies
_MAX_FALLBACK = 5000
_fallback_rate_limits = OrderedDict()

async def create_session(user_data: dict):
    """Creates a Redis session with MongoDB fallback."""
    user_id = user_data.get('id')
    if not user_id:
        user_json = json.loads(user_data.get('user', '{}'))
        user_id = user_json.get('id')
        
    if not user_id:
        return None
        
    token = str(uuid.uuid4())
    session_key = f"user_session:{user_id}"
    token_key = f"auth_token:{token}"
    
    if not r:
        expiry = time.time() + 3600
        await sessions_collection.update_one(
            {"_id": session_key},
            {"$set": {"token": token, "expires_at": expiry}},
            upsert=True
        )
        await sessions_collection.update_one(
            {"_id": token_key},
            {"$set": {"user_id": str(user_id), "expires_at": expiry}},
            upsert=True
        )
        return token, user_id
        
    # Store both mappings
    await r.setex(session_key, 3600, token)
    await r.setex(token_key, 3600, str(user_id))
    
    return token, user_id

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """Middleware to validate session and handle rate limiting."""
    token = auth.credentials
    if not r:
        token_doc = await sessions_collection.find_one({"_id": f"auth_token:{token}"})
        if not token_doc or token_doc.get("expires_at", 0) < time.time():
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        raw = token_doc.get("user_id", "")
        try:
            return int(str(raw).strip())
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid session data")

    user_id = await r.get(f"auth_token:{token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    # Rate Limiting: 30 req / 60s (sliding window)
    now = time.time()
    rate_key = f"rate_limit:{user_id}"
    
    try:
        async with r.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(rate_key, 0, now - 60)
            pipe.zadd(rate_key, {str(now): now})
            pipe.zcard(rate_key)
            pipe.expire(rate_key, 60)
            _, _, count, _ = await pipe.execute()
            
        if count > 30:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logging.warning(f"Rate limiting skipped due to Redis error, using local fallback: {e}")
        
        # Enforce LRU cleanup to avoid memory leak if Redis falls over
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

async def get_current_user_data(user_id: int = Depends(get_current_user)):
    """Dependency to fetch the full user document."""
    user = await user_collection.find_one({"id": int(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
