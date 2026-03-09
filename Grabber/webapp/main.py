from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from Grabber.webapp.auth import validate_init_data, create_session, r
from Grabber.webapp.api import router as api_router
from Grabber.webapp.ws import router as ws_router
import os
import logging

app = FastAPI(title="Telegram WebApp API")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support if the issue persists."},
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://dear-project-01-seal-6d4f0ddd98e4.herokuapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth")
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
    
    # Also store the token -> user_id mapping for fast auth
    await r.setex(f"auth_token:{token}", 3600, user_id)
    
    return {"token": token}

# Include routers
app.include_router(api_router)
app.include_router(ws_router)

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    # Development fallback or warning
    pass
