from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from Grabber.webapp.auth import validate_init_data, create_session, r
from Grabber.webapp.api import router as api_router
from Grabber.webapp.ws import router as ws_router
from Grabber import start_bots, stop_bots
from config import config
from contextlib import asynccontextmanager
import os
import logging

import asyncio
from Grabber.core.cache import rebuild_leaderboard
from Grabber.database import user_collection

async def sync_leaderboard_periodic():
    """Background task to keep the Redis Top 1000 in sync with Mongo."""
    while True:
        try:
            await rebuild_leaderboard(user_collection)
        except Exception as e:
            logging.error(f"Error in periodic leaderboard sync: {e}")
        # Sync every hour (3600 seconds)
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the Telegram bots and the rank sync task
    logging.info("Starting Telegram bots and ranking sync task...")
    await start_bots()
    sync_task = asyncio.create_task(sync_leaderboard_periodic())
    
    yield
    
    # Shutdown: Stop the Telegram bots and our sync task
    logging.info("Stopping Telegram bots and background tasks...")
    sync_task.cancel()
    await stop_bots()

app = FastAPI(
    title="Telegram WebApp API",
    docs_url=None, 
    redoc_url=None, 
    openapi_url=None,
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support if the issue persists."})

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", config.WEB_APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# Add GZip Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject basic security headers into every API response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Note: X-Frame-Options must NOT be 'DENY' for Telegram Mini Apps to function in a frame.
    return response

@api_router.post("/secure_init")
async def auth(request: Request):
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
        if not r:
            from Grabber.database import sessions_collection
            import time as _time
            token_doc = await sessions_collection.find_one({"_id": f"auth_token:{token_provided}"})
            if token_doc and token_doc.get("expires_at", 0) > _time.time():
                user_id = token_doc.get("user_id")
                new_token = token_provided
        else:
            user_id = await r.get(f"auth_token:{token_provided}")
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
            if await r.get(sync_key):
                should_sync = False
        except Exception:
            pass

    if should_sync:
        # Update Avatar and Name in DB
        updates = {}
        if avatar_url:
            updates["avatar"] = avatar_url
            
        if init_data:
            try:
                import json
                from urllib.parse import parse_qsl
                vals = dict(parse_qsl(init_data))
                if 'user' in vals:
                    uobj = json.loads(vals['user'])
                    if uobj.get('first_name'): 
                        updates['first_name'] = uobj['first_name']
                    if uobj.get('username'): 
                        updates['username'] = uobj['username']
            except Exception:
                pass
                
        if updates:
            from Grabber.database import user_collection
            await user_collection.update_one(
                {"id": {"$in": [user_id, str(user_id)]}},
                {"$set": updates}
            )
            if r:
                try: await r.setex(sync_key, 3600, "1")
                except: pass
    
    return {"token": new_token}


# Include routers with obfuscated prefix
api_version_prefix = os.getenv("API_VERSION_PREFIX", "v1_7b82")
app.include_router(api_router, prefix=f"/api/{api_version_prefix}")
app.include_router(ws_router, prefix=f"/api/{api_version_prefix}")

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # Allow API and assets to pass through
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            return None # FastAPI will continue to other routes
            
        index_file = os.path.join(frontend_path, "index.html")
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
else:
    # Development fallback or warning
    pass
