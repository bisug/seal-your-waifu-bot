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
        except Exception:
            pass
