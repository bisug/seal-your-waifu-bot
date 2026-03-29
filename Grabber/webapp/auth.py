import hmac
import hashlib
import json
import uuid
import time
import logging
from urllib.parse import parse_qsl
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Grabber.database import r, sessions_collection, user_collection
from config import config

security = HTTPBearer()

def validate_init_data(init_data: str):
    """
    Validates the data received from the Telegram Web App.
    Based on: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
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

from collections import defaultdict
_fallback_rate_limits = defaultdict(list)

async def create_session(user_data: dict):
    """Creates a Redis session for the user."""
    user_id = user_data.get('id')
    if not user_id:
        # Extract user_id from json string if needed
        user_json = json.loads(user_data.get('user', '{}'))
        user_id = user_json.get('id')
        
    if not user_id:
        return None
        
    token = str(uuid.uuid4())
    session_key = f"user_session:{user_id}"
    token_key = f"auth_token:{token}"
    
    if not r:
        expiry = time.time() + 3600
        # Store in MongoDB for fallback support
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
    """Middleware to validate session token and handle rate limiting."""
    token = auth.credentials
    if not r:
        token_doc = await sessions_collection.find_one({"_id": f"auth_token:{token}"})
        if not token_doc or token_doc.get("expires_at", 0) < time.time():
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        return int(token_doc["user_id"])

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
        
        # Periodically clean up old rate limit entries to avoid memory leak
        if len(_fallback_rate_limits) > 1000:
            stale = [uid for uid, hist in list(_fallback_rate_limits.items()) if not [ts for ts in hist if now - ts < 60]]
            for uid in stale:
                if uid in _fallback_rate_limits:
                    del _fallback_rate_limits[uid]
                    
        history = _fallback_rate_limits[user_id]
        history = [ts for ts in history if now - ts < 60]
        if len(history) >= 30:
            _fallback_rate_limits[user_id] = history
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
        history.append(now)
        _fallback_rate_limits[user_id] = history

    return int(user_id)

async def get_current_user_data(user_id: int = Depends(get_current_user)):
    """Dependency to fetch the full user document from the database efficiently."""
    # Provide a unified way to fetch the DB object and replace scattered queries
    user = await user_collection.find_one({"id": int(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
