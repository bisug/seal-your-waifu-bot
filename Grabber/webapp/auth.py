import hmac
import hashlib
import json
import uuid
import time
from urllib.parse import parse_qsl
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Grabber.database import r
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
        
        secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
        h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(h, msg_hash):
            return vals
    except Exception:
        pass
    return False

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
    session_key = f"session:{user_id}"
    
    # Store token in Redis with TTL
    await r.setex(session_key, 3600, token)
    return token, user_id

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """Middleware to validate session token and handle rate limiting."""
    token = auth.credentials
    # This is simplified; in production, you'd need the user_id to check the session
    # We can encode user_id in the token or use a separate lookup
    # For this implementation, we'll use a token:user_id mapping in Redis for fast lookup
    user_id = await r.get(f"auth_token:{token}")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    # Rate Limiting: 30 req / 60s (sliding window)
    now = time.time()
    rate_key = f"rate_limit:{user_id}"
    
    async with r.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(rate_key, 0, now - 60)
        pipe.zadd(rate_key, {str(now): now})
        pipe.zcard(rate_key)
        pipe.expire(rate_key, 60)
        _, _, count, _ = await pipe.execute()
        
    if count > 30:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
        
    return int(user_id)
