from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from Grabber.core.cache import invalidate_user_cache, sync_user_to_redis
from Grabber.core.eggs import get_incubation_wait_minutes
from Grabber.core.utils import (get_now_utc, get_user_id_query,
                                normalize_user_id)
from Grabber.database import user_collection
from Grabber.core.pets import (
    DEFAULT_PET,
    ensure_user_pet_state,
    find_pet,
    get_pet_key,
    normalize_pet,
)
from Grabber.modules.progression.quests import (QUEST_POOL, WEEKLY_POOL,
                                                add_xp, get_user_quests)
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.webapp.schemas import QuestsResponse

router = APIRouter()



@router.get("/quests", response_model=QuestsResponse)
async def get_quests(user_id: int = Depends(get_current_user)):
    quests_data = await get_user_quests(user_id)
    
    response = {"daily": [], "weekly": []}
    
    for qid, qdata in quests_data.items():
        if qid in QUEST_POOL:
            info = QUEST_POOL[qid].copy()
            info["id"] = qid
            info.update(qdata)
            response["daily"].append(info)
        elif qid in WEEKLY_POOL:
            info = WEEKLY_POOL[qid].copy()
            info["id"] = qid
            info.update(qdata)
            response["weekly"].append(info)
            
    return response

@router.post("/quests/claim/{quest_id}")
async def claim_quest(quest_id: str, user_id: int = Depends(get_current_user)):
    quests = await get_user_quests(user_id)
    if quest_id not in quests:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    qdata = quests[quest_id]
    if qdata.get("claimed"):
        raise HTTPException(status_code=400, detail="Already claimed")
        
    info = QUEST_POOL.get(quest_id) or WEEKLY_POOL.get(quest_id)
    if qdata.get("progress", 0) < info["target"]:
        raise HTTPException(status_code=400, detail="Quest not completed")
        
    # Atomic update to prevent race conditions during rapid concurrent requests
    q = get_user_id_query(user_id)
    q[f"quests.{quest_id}.claimed"] = {"$ne": True}
    
    result = await user_collection.update_one(
        q,
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Already claimed or processing")
        
    await add_xp(user_id, info["reward_xp"], f"quest_{quest_id}")
    reward_shards = info.get("reward_shards", 0)
    if reward_shards > 0:
        await user_collection.update_one(
            get_user_id_query(user_id),
            {"$inc": {"balance": reward_shards}}
        )

    await sync_user_to_redis(user_id)
    
    return {"success": True, "reward_xp": info["reward_xp"], "reward_shards": reward_shards}

@router.post("/pets/set_active/{pet_ref}")
async def set_active_pet(pet_ref: str, user: dict = Depends(get_current_user_data)):
    uid_int = normalize_user_id(user["id"])
    user = await ensure_user_pet_state(uid_int, user)
    pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
    pet = find_pet(pets, pet_ref)
    if not pet:
        raise HTTPException(status_code=400, detail="Pet not owned")

    pet_key = get_pet_key(pet)
    await user_collection.update_one(
        get_user_id_query(uid_int),
        {"$set": {"current_pet": pet_key}}
    )
    await invalidate_user_cache(uid_int)
    return {"status": "success", "pet": pet_key}

@router.post("/eggs/incubate/{egg_id}")
async def incubate_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    uid_int = normalize_user_id(user["id"])
    
    fresh_user = await user_collection.find_one(get_user_id_query(uid_int))
    if not fresh_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    eggs = fresh_user.get("eggs", [])
    egg = next((e for e in eggs if isinstance(e, dict) and e.get("id") == egg_id), None)
    if not egg:
        raise HTTPException(status_code=404, detail="Egg not found")
        
    if egg.get("status") != "fresh":
        raise HTTPException(status_code=400, detail="Egg already incubating or hatched")
        
    fresh_user = await ensure_user_pet_state(uid_int, fresh_user)
    pets = [normalize_pet(p) for p in fresh_user.get("pets", [DEFAULT_PET])]
    active_pet = find_pet(pets, fresh_user.get("current_pet"))
    wait_min = get_incubation_wait_minutes(egg.get("tier", "common"), active_pet)
        
    ready_time = get_now_utc() + timedelta(minutes=wait_min)
    
    q = get_user_id_query(uid_int)
    # Ensure egg is exactly in 'fresh' state to avoid double incubation
    q["eggs"] = {"$elemMatch": {"id": egg_id, "status": "fresh"}}
    res = await user_collection.update_one(
        q,
        {
            "$set": {
                "eggs.$.status": "incubating",
                "eggs.$.hatch_time": ready_time
            }
        }
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Egg status changed concurrently. Please refresh.")
        
    return {"status": "success", "ready_at": ready_time.isoformat(), "wait_min": wait_min}

@router.post("/eggs/hatch/{egg_id}")
async def hatch_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    from Grabber.modules.economy.hunt import process_egg_hatch

    uid_int = normalize_user_id(user["id"])

    fresh_user = await user_collection.find_one(get_user_id_query(uid_int))
    if not fresh_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    eggs = fresh_user.get("eggs", [])
    egg = next((e for e in eggs if isinstance(e, dict) and e.get("id") == egg_id), None)
    
    if not egg or egg.get("status") != "incubating":
         raise HTTPException(status_code=400, detail="Egg not ready or not found")
         
    h_time = egg.get("hatch_time")
    if h_time and get_now_utc().replace(tzinfo=None) < h_time.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Egg still incubating")

    # Atomic guarantees are handled gracefully inside process_egg_hatch without locks
    success, result = await process_egg_hatch(uid_int, egg)
    
    if not success:
        msg = result.replace("<b>", "").replace("</b>", "").replace("💥 ", "").replace("⚠️ ", "").replace("\n", " ")
        raise HTTPException(status_code=422, detail=msg)
         
    character = result
    return {
        "status": "success",
        "character": {
            "id": character["id"],
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "img_url": character["img_url"]
        }
    }
