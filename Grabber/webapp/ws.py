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

    # Validate token from query param before proceeding
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_text(json.dumps({"error": "Unauthorized: no token"}))
        await websocket.close(code=4001)
        return

    # Validate token against Redis/MongoDB session store
    if r:
        user_id = await r.get(f"auth_token:{token}")
    else:
        from Grabber.database import sessions_collection
        import time as _time
        doc = await sessions_collection.find_one({"_id": f"auth_token:{token}"})
        user_id = doc.get("user_id") if doc and doc.get("expires_at", 0) > _time.time() else None

    if not user_id:
        await websocket.send_text(json.dumps({"error": "Unauthorized: invalid or expired token"}))
        await websocket.close(code=4001)
        return

    # Subscribe to leaderboard changes in Redis
    pubsub = r.pubsub()
    await pubsub.subscribe("leaderboard_updates")
    
    async def listen_redis():
        """Efficiently listen for Redis pub/sub messages."""
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message.get("data")
                if data:
                    await websocket.send_text(data if isinstance(data, str) else data.decode())

    async def listen_client():
        """Wait for client disconnect."""
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    try:
        # Run both listeners concurrently; when either finishes, cancel the other
        redis_task = asyncio.create_task(listen_redis())
        client_task = asyncio.create_task(listen_client())
        done, pending = await asyncio.wait(
            [redis_task, client_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        await pubsub.unsubscribe("leaderboard_updates")
        try:
            await websocket.close()
        except Exception as e:
            from Grabber import LOGGER
            LOGGER.debug(f"Websocket close error: {e}")
