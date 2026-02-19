from typing import Optional, Dict, Any
from Grabber.database import sessions_collection

async def create_session(session_id: str, data: Dict[str, Any], expire_after: int = 3600):
\
\
\
\
       
    import time
    data["_id"] = session_id
    data["created_at"] = time.time()
    await sessions_collection.replace_one({"_id": session_id}, data, upsert=True)

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return await sessions_collection.find_one({"_id": session_id})

async def delete_session(session_id: str):
    await sessions_collection.delete_one({"_id": session_id})
