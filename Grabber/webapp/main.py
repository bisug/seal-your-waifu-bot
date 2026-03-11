from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from Grabber.webapp.auth import validate_init_data, create_session, r
from Grabber.webapp.api import router as api_router
from Grabber.webapp.ws import router as ws_router
from Grabber import start_bots, stop_bots
from config import config
from contextlib import asynccontextmanager
import os
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the Telegram bots
    logging.info("Starting Telegram bots...")
    await start_bots()
    yield
    # Shutdown: Stop the Telegram bots
    logging.info("Stopping Telegram bots...")
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

@api_router.post("/secure_init")
async def auth(request: Request):
    data = await request.json()
    init_data = data.get("initData")
    
    validated_data = validate_init_data(init_data)
    if not validated_data:
        raise HTTPException(status_code=403, detail="Invalid Telegram initialization data")
        
    session_data = await create_session(validated_data)
    if not session_data:
        raise HTTPException(status_code=500, detail="Failed to create session")
        
    token, user_id = session_data
    
    return {"token": token}

# Include routers with obfuscated prefix
api_version_prefix = os.getenv("API_VERSION_PREFIX", "v1_7b82")
app.include_router(api_router, prefix=f"/api/{api_version_prefix}")
app.include_router(ws_router, prefix=f"/api/{api_version_prefix}")

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    # Development fallback or warning
    pass
