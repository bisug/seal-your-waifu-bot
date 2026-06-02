import asyncio
import json
import time as _time
from collections import OrderedDict
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request

from Grabber import LOGGER
from Grabber.core.user import add_user_set_on_insert, get_user_filter
from Grabber.database import user_collection
from Grabber.webapp.auth import create_session, get_user_id_from_token, r, validate_init_data

router = APIRouter()

_MAX_INIT_FALLBACK = 5000
_init_rate_limits: OrderedDict[str, list[float]] = OrderedDict()

async def check_init_rate_limit(request: Request):
    """IP-based rate limit for /secure_init: 10 req/60s per IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = _time.time()
    rate_key = f"rl_init:{client_ip}"

    if r:
        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(rate_key, 0, now - 60)
                pipe.zadd(rate_key, {str(now): now})
                pipe.zcard(rate_key)
                pipe.expire(rate_key, 60)
                _, _, count, _ = await asyncio.wait_for(pipe.execute(), timeout=3.0)
            if count > 10:
                raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
            return
        except HTTPException:
            raise
        except Exception:
            pass  # Redis error: fall through to local fallback

    # Local fallback
    history = [ts for ts in _init_rate_limits.get(client_ip, []) if now - ts < 60]
    if len(history) >= 10:
        _init_rate_limits[client_ip] = history
        _init_rate_limits.move_to_end(client_ip)
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    history.append(now)
    _init_rate_limits[client_ip] = history
    _init_rate_limits.move_to_end(client_ip)
    while len(_init_rate_limits) > _MAX_INIT_FALLBACK:
        _init_rate_limits.popitem(last=False)

@router.post("/secure_init")
async def auth(request: Request, _: None = Depends(check_init_rate_limit)):
    data = await request.json()
    init_data = data.get("initData")
    token_provided = data.get("token")
    avatar_url = data.get("avatar")
    
    user_id = None
    new_token = None

    if init_data:
        validated_data = validate_init_data(init_data)
        if validated_data:
            session_data = await create_session(validated_data)
            if session_data:
                new_token, user_id = session_data
    
    # Fallback to provided token if init_data is missing or invalid
    if not user_id and token_provided:
        user_id = await get_user_id_from_token(token_provided)
        if user_id:
            new_token = token_provided
            user_id = str(user_id)

    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication failed. Please open the bot in PM.")

    # Optimization: Only sync profile once per hour to avoid redundant DB writes
    sync_key = f"last_sync:{user_id}"
    should_sync = True
    if r:
        try:
            if await asyncio.wait_for(r.get(sync_key), timeout=3.0):
                should_sync = False
        except Exception as e:
            LOGGER.debug(f"Redis sync check failed: {e}")

    if should_sync:
        # Update Avatar and Name in DB
        updates = {}
        if avatar_url:
            updates["avatar"] = avatar_url
            
        if init_data:
            try:
                vals = dict(parse_qsl(init_data))
                if 'user' in vals:
                    uobj = json.loads(vals['user'])
                    if uobj.get('first_name'): 
                        updates['first_name'] = uobj['first_name']
                    if uobj.get('username'): 
                        updates['username'] = uobj['username']
            except Exception as e:
                LOGGER.debug(f"InitData payload unparseable: {e}")
                
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            user_id_int = user_id
        try:
            user_update = {}
            if updates:
                user_update["$set"] = updates
            add_user_set_on_insert(
                user_update,
                user_id_int,
                first_name=updates.get("first_name"),
                username=updates.get("username"),
            )
            await user_collection.update_one(
                get_user_filter(user_id_int),
                user_update,
                upsert=True,
            )
            if r:
                try: await asyncio.wait_for(r.setex(sync_key, 3600, "1"), timeout=3.0)
                except Exception as e: 
                    LOGGER.debug(f"Redis string write failed: {e}")
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid user id in session.")
    
    return {"token": new_token}
