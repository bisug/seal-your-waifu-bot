from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from Grabber.database import r
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/leaderboard")
async def leaderboard_ws(websocket: WebSocket):
    await websocket.accept()

    # Fix #6: Guard against Redis being None (e.g. REDIS_URL not configured)
    if not r:
        await websocket.send_text(json.dumps({"error": "Realtime updates unavailable: Redis not configured"}))
        await websocket.close(code=1011)
        return

    # Send initial data
    # (Initial data would normally be fetched here)
    
    # Subscribe to leaderboard changes in Redis
    pubsub = r.pubsub()
    await pubsub.subscribe("leaderboard_updates")
    
    try:
        while True:
            # Check for messages from Redis
            message = await pubsub.get_message(ignore_subscribe_none=True)
            if message:
                data = message.get("data")
                if data:
                    await websocket.send_text(data)
            
            # Keep-alive or check for client messages
            try:
                # Use a small timeout to not block the pubsub check
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                # Handle client messages if any
            except asyncio.TimeoutError:
                pass
                
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        await pubsub.unsubscribe("leaderboard_updates")
    except Exception:
        await pubsub.unsubscribe("leaderboard_updates")
        await websocket.close()
