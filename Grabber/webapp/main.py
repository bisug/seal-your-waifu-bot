from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.gzip import GZipMiddleware
from Grabber.webapp.auth import validate_init_data, create_session, r
from Grabber.webapp.api import router as api_router
from Grabber.webapp.ws import router as ws_router
from Grabber.runner import start_bots, stop_bots
from Grabber import LOGGER
from config import config
from contextlib import asynccontextmanager
import os
import logging
import asyncio

from Grabber.core.cache import rebuild_leaderboard
from Grabber.core.worker import background_maintenance
from Grabber.database import user_collection

_lb_rebuild_in_progress = False

async def sync_leaderboard_periodic():
    """Background task to keep the Redis Top 1000 in sync with Mongo for all metrics."""
    global _lb_rebuild_in_progress
    await asyncio.sleep(60) # Delay on startup to allow app to settle
    metrics = ["level", "harem", "shards", "zenith", "guesses"]
    while True:
        if not _lb_rebuild_in_progress:
            _lb_rebuild_in_progress = True
            try:
                for metric in metrics:
                    await rebuild_leaderboard(user_collection, metric=metric)
                    await asyncio.sleep(2) # Smooth out IO bursts
            except Exception as e:
                logging.error(f"Error in periodic leaderboard sync: {e}")
            finally:
                _lb_rebuild_in_progress = False
        # Sync every hour (3600 seconds)
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the Telegram bots and the rank sync task
    logging.info("Starting Telegram bots and ranking sync task...")
    await start_bots()
    sync_task = asyncio.create_task(sync_leaderboard_periodic())
    worker_task = asyncio.create_task(background_maintenance())
    
    yield
    
    # Shutdown: Stop the Telegram bots and our sync task
    logging.info("Stopping Telegram bots and background tasks...")
    sync_task.cancel()
    worker_task.cancel()
    await stop_bots()

app = FastAPI(
    title="Telegram WebApp API",
    docs_url=None, 
    redoc_url=None, 
    openapi_url=None,
    lifespan=lifespan
)

from fastapi import HTTPException as FastAPIHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, FastAPIHTTPException):
        raise exc
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

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

# Include routers with obfuscated prefix
api_version_prefix = os.getenv("API_VERSION_PREFIX", "v1_7b82")
app.include_router(api_router, prefix=f"/api/{api_version_prefix}")
app.include_router(ws_router, prefix=f"/api/{api_version_prefix}")

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(request: Request, full_path: str):
        # Critical Protection: Do NOT intercept API or Asset calls.
        api_prefix = f"api/{api_version_prefix}"
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            # If we reached here for an API/Asset path, it means the actual route doesn't exist.
            raise HTTPException(status_code=404, detail="Resource not found")
            
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)
else:
    LOGGER.warning("Frontend UI missing: React build missing or inactive.")
