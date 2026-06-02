import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from Grabber.database import r
from Grabber.webapp.auth import get_user_id_from_token

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

    # Validate token through Redis first, with MongoDB auth-session fallback.
    user_id = await get_user_id_from_token(token)

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

    async def heartbeat():
        """Send a ping every 25s to keep the connection alive through proxies."""
        try:
            while True:
                await asyncio.sleep(25)
                await websocket.send_text('{"type":"ping"}')
        except Exception:
            pass  # Swallow — connection closed normally

    try:
        # Run listeners concurrently; when any finishes, cancel the others
        redis_task = asyncio.create_task(listen_redis())
        client_task = asyncio.create_task(listen_client())
        hb_task = asyncio.create_task(heartbeat())
        done, pending = await asyncio.wait(
            [redis_task, client_task, hb_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        # FIX: Unsubscribe and fully close the pubsub connection in its own
        # try/except so that a WebSocketDisconnect from websocket.close()
        # below cannot skip aclose() and leak the Redis subscription.
        try:
            await pubsub.unsubscribe("leaderboard_updates")
            await pubsub.aclose()
        except Exception as e:
            from Grabber import LOGGER
            LOGGER.debug(f"Pubsub teardown error: {e}")
        try:
            await websocket.close()
        except Exception as e:
            from Grabber import LOGGER
            LOGGER.debug(f"Websocket close error: {e}")
