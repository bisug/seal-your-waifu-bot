import asyncio
import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import config
from backend import LOGGER
from backend.core.cache import (
    consume_leaderboard_dirty,
    get_total_ranked_users,
    mark_leaderboard_dirty,
    rebuild_leaderboard,
)
from backend.core.logging import (
    configure_event_loop_logging,
    new_request_id,
    reset_request_id,
    set_request_id,
)
from backend.core.resources import get_resource_snapshot, pressure_reason
from backend.core.tasks import run_background_task
from backend.core.worker import background_maintenance
from backend.database import r, seal_db, user_collection
from backend import runner
from backend.runner import start_bots, stop_bots
from backend.webapp.api import router as api_router
from backend.webapp.errors import error_response
from backend.webapp.ws import router as ws_router


async def sync_leaderboard_periodic():
    """Sync Redis ZSETs with MongoDB periodically.

    Only rebuilds metrics flagged dirty (e.g. an instant sync failed) or
    ZSETs that are empty. sync_user_to_redis keeps healthy ZSETs fresh, so
    unconditional hourly rebuilds were wasted IO.
    """
    await asyncio.sleep(60) # Delay on startup to allow app to settle
    metrics = ["level", "harem", "shards", "zenith", "guesses"]
    while True:
        for metric in metrics:
            try:
                dirty = consume_leaderboard_dirty(metric)
                empty = (await get_total_ranked_users(metric)) == 0
                if not dirty and not empty:
                    continue
                await rebuild_leaderboard(user_collection, metric=metric)
                await asyncio.sleep(2) # Smooth out IO bursts
            except Exception as e:
                LOGGER.exception(f"Error in periodic leaderboard sync [{metric}]: {e}")
                mark_leaderboard_dirty([metric])  # Retry on the next cycle
        # Sync every hour (3600 seconds)
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_event_loop_logging()
    # Do NOT await the bots here: Render's zero-downtime deploy only stops
    # the old instance after this one passes its health check, but the old
    # instance holds the single-instance lock until it exits. Blocking the
    # lifespan on start_bots() deadlocks the deploy and the new container
    # gives up after the wait timeout. Start the web server immediately and
    # let the bots start in the background once the lock frees up.
    bot_task = run_background_task(start_bots(), name="bot-startup")
    sync_task = run_background_task(sync_leaderboard_periodic(), name="leaderboard-sync")
    worker_task = run_background_task(background_maintenance(), name="background-maintenance")

    try:
        yield
    finally:
        # Gracefully cancel background tasks before stopping bots
        bot_task.cancel()
        sync_task.cancel()
        worker_task.cancel()
        await asyncio.gather(bot_task, sync_task, worker_task, return_exceptions=True)
        await stop_bots()

app = FastAPI(
    title="Telegram WebApp API",
    docs_url=None, 
    redoc_url=None, 
    openapi_url=None,
    lifespan=lifespan
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response(
        request,
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers,
        fallback_message="Request failed",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        request,
        status_code=422,
        detail=exc.errors(),
        code="validation_error",
        fallback_message="Validation failed",
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    return error_response(
        request,
        status_code=400,
        detail="Malformed JSON body",
        code="malformed_json",
        fallback_message="Malformed JSON body",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    LOGGER.error("Unhandled API exception", exc_info=(type(exc), exc, exc.__traceback__))
    return error_response(
        request,
        status_code=500,
        detail="Internal server error. Please contact support if the issue persists.",
        code="internal_error",
        fallback_message="Internal server error",
    )

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
    """Inject basic security headers."""
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    request.state.request_id = request_id
    context_token = set_request_id(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "img-src 'self' data: https: http:; "
            "media-src 'self' https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "script-src 'self' https://telegram.org https://*.telegram.org; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors https://web.telegram.org https://*.telegram.org"
        )
        duration_ms = (time.perf_counter() - started) * 1000
        log = LOGGER.debug if request.url.path in {"/healthz", "/readyz"} else LOGGER.info
        log(
            "HTTP %s %s -> %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        # Note: X-Frame-Options must NOT be 'DENY' for Telegram Mini Apps to function in a frame.
        return response
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        LOGGER.exception("HTTP %s %s failed after %.2fms", request.method, request.url.path, duration_ms)
        raise
    finally:
        reset_request_id(context_token)

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}


@app.get("/readyz")
async def readiness_check():
    checks = {"mongo": "ok", "redis": "disabled", "bots": runner.STARTUP_STATE}
    status_code = 200

    try:
        await seal_db.ping()
    except Exception as e:
        checks["mongo"] = f"error: {type(e).__name__}"
        status_code = 503

    if r:
        try:
            await asyncio.wait_for(r.ping(), timeout=3.0)
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {type(e).__name__}"
            status_code = 503

    try:
        snapshot = get_resource_snapshot()
        reason = pressure_reason(snapshot)
        checks["resources"] = {
            "status": "degraded" if reason else "ok",
            "reason": reason,
            "rss_mb": snapshot.rss_mb,
            "available_mb": snapshot.available_mb,
            "tasks": snapshot.task_count,
            "fd_count": snapshot.fd_count,
            "soft_limit_mb": snapshot.soft_limit_mb,
            "hard_limit_mb": snapshot.hard_limit_mb,
        }
        if reason == "hard_memory_limit":
            status_code = 503
    except Exception as e:
        checks["resources"] = f"error: {type(e).__name__}"

    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if status_code == 200 else "degraded", "checks": checks},
    )

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
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            raise HTTPException(status_code=404, detail="Resource not found")
            
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)
else:
    LOGGER.warning("Frontend UI missing: React build missing or inactive.")
