from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from backend.core.cache import invalidate_user_cache
from backend.core.eggs import get_incubating_count, get_incubation_wait_minutes
from backend.core.leaderboard import sync_user_to_redis
from backend.core.pass_config import (
    apply_pass_incubation_bonus,
    get_active_pass_type,
    get_pass_incubation_slots,
)
from backend.core.utils import get_now_utc, get_user_id_query, normalize_user_id
from backend.database import user_collection
from backend.modules.progression.quests import (
    PASS_MISSIONS,
    QUEST_POOL,
    WEEKLY_POOL,
    add_xp,
    get_user_quests,
)
from backend.webapp.auth import get_current_user, get_current_user_data
from backend.webapp.schemas import QuestsResponse

router = APIRouter()



@router.get("/quests", response_model=QuestsResponse)
async def get_quests(user_id: int = Depends(get_current_user)):
    quests_data = await get_user_quests(user_id)
    
    user = await user_collection.find_one(get_user_id_query(user_id)) or {}
    pass_type = get_active_pass_type(user)
    response = {"daily": [], "weekly": [], "pass": [], "pass_type": pass_type}
    
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
        elif qid in PASS_MISSIONS:
            info = PASS_MISSIONS[qid].copy()
            info["id"] = qid
            info["locked"] = pass_type == "free"
            info.update(qdata)
            response["pass"].append(info)
            
    return response

@router.post("/quests/claim/{quest_id}")
async def claim_quest(quest_id: str, user_id: int = Depends(get_current_user)):
    quests = await get_user_quests(user_id)
    if quest_id not in quests:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    qdata = quests[quest_id]
    if qdata.get("claimed"):
        raise HTTPException(status_code=400, detail="Already claimed")
        
    info = QUEST_POOL.get(quest_id) or WEEKLY_POOL.get(quest_id) or PASS_MISSIONS.get(quest_id)
    if quest_id in PASS_MISSIONS:
        user = await user_collection.find_one(get_user_id_query(user_id)) or {}
        if get_active_pass_type(user) == "free":
            raise HTTPException(status_code=400, detail="This mission requires Premium or Elite Pass")
    if not info:
        raise HTTPException(status_code=404, detail="Quest not found")
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
    active_incubations = get_incubating_count(eggs)
    slots = get_pass_incubation_slots(fresh_user)
    if active_incubations >= slots:
        raise HTTPException(status_code=400, detail=f"All incubators are busy ({active_incubations}/{slots})")

    base_wait_min = get_incubation_wait_minutes(egg.get("tier", "common"))
    wait_min = apply_pass_incubation_bonus(base_wait_min, fresh_user)
        
    ready_time = get_now_utc() + timedelta(minutes=wait_min)
    
    q = get_user_id_query(uid_int)
    # Ensure egg is exactly in 'fresh' state to avoid double incubation
    q["eggs"] = {"$elemMatch": {"id": egg_id, "status": "fresh"}}
    # Atomic slot guard: the pre-check above reads a stale snapshot, so two
    # concurrent requests could both pass it. Re-check inside the filter.
    q["$expr"] = {
        "$lt": [
            {"$size": {"$filter": {
                "input": {"$ifNull": ["$eggs", []]},
                "as": "e",
                "cond": {"$eq": ["$$e.status", "incubating"]},
            }}},
            slots,
        ]
    }
    res = await user_collection.update_one(
        q,
        {
            "$set": {
                "eggs.$.status": "incubating",
                "eggs.$.hatch_time": ready_time,
                "eggs.$.incubation_started_at": get_now_utc(),
                "eggs.$.incubation_base_minutes": base_wait_min,
                "eggs.$.incubation_minutes": wait_min,
                "eggs.$.incubation_pass_type": get_active_pass_type(fresh_user)
            }
        }
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Egg status changed concurrently. Please refresh.")
        
    return {
        "status": "success",
        "ready_at": ready_time.isoformat(),
        "wait_min": wait_min,
        "base_wait_min": base_wait_min,
        "incubation_slots": slots,
        "active_incubations": active_incubations + 1,
    }

@router.post("/eggs/hatch/{egg_id}")
async def hatch_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    from backend.modules.economy.hunt import process_egg_hatch

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

@router.post("/eggs/sell/{egg_id}")
async def sell_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    from backend.modules.economy.hunt import process_egg_sell

    uid_int = normalize_user_id(user["id"])
    success, msg, price = await process_egg_sell(uid_int, egg_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg.replace("<b>", "").replace("</b>", ""))
    await invalidate_user_cache(uid_int)
    return {"status": "success", "price": price, "message": msg.replace("<b>", "").replace("</b>", "")}

@router.post("/eggs/purify/{egg_id}")
async def purify_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    from backend.modules.economy.hunt import process_egg_purify

    uid_int = normalize_user_id(user["id"])
    success, msg = await process_egg_purify(uid_int, egg_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg.replace("<b>", "").replace("</b>", ""))
    await invalidate_user_cache(uid_int)
    return {"status": "success", "message": msg.replace("<b>", "").replace("</b>", "")}

@router.post("/eggs/fuse/{tier}")
async def fuse_eggs(tier: str, user: dict = Depends(get_current_user_data)):
    from backend.modules.economy.hunt import process_egg_fusion

    uid_int = normalize_user_id(user["id"])
    success, msg = await process_egg_fusion(uid_int, tier)
    if not success:
        raise HTTPException(status_code=400, detail=msg.replace("<b>", "").replace("</b>", ""))
    await invalidate_user_cache(uid_int)
    return {"status": "success", "message": msg.replace("<b>", "").replace("</b>", "")}
