from typing import Optional, Dict, Any
from Grabber.database import sessions_collection

async def create_session(session_id: str, data: Dict[str, Any], expire_after: int = 3600):
    """
    Create a temporary session in MongoDB.
    session_id: uniquely identifying the session (e.g., "battle_uid1_uid2")
    expire_after: seconds after which the session might be considered stale (manual check or TTL index)
    """
    import time
    data["_id"] = session_id
    data["created_at"] = time.time()
    await sessions_collection.replace_one({"_id": session_id}, data, upsert=True)

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return await sessions_collection.find_one({"_id": session_id})

async def delete_session(session_id: str):
    await sessions_collection.delete_one({"_id": session_id})
