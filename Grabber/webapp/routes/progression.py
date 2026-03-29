from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.database import user_collection
from Grabber.webapp.models import QuestsResponse
from Grabber.modules.progression.quests import get_user_quests, QUEST_POOL, WEEKLY_POOL, add_xp
from Grabber.core.constants import EGG_TIERS
from Grabber.modules.progression.pet import DEFAULT_PET

router = APIRouter()

def get_user_id_query(user_id):
    try:
        uid_int = int(user_id)
        return {"id": {"$in": [uid_int, str(uid_int)]}}
    except (ValueError, TypeError):
        return {"id": str(user_id)}

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
        
    await add_xp(user_id, info["reward_xp"], f"quest_{quest_id}")
    await user_collection.update_one(
        get_user_id_query(user_id),
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    
    return {"success": True, "reward_xp": info["reward_xp"]}

@router.post("/pets/set_active/{pet_name}")
async def set_active_pet(pet_name: str, user: dict = Depends(get_current_user_data)):
    pets = user.get("pets", [DEFAULT_PET])
    if not any(p["name"] == pet_name for p in pets):
        raise HTTPException(status_code=400, detail="Pet not owned")
        
    uid_int = user["id"]
    if isinstance(uid_int, list): uid_int = uid_int[0]

    await user_collection.update_one(
        get_user_id_query(uid_int),
        {"$set": {"current_pet": pet_name}}
    )
    return {"status": "success", "pet": pet_name}

@router.post("/eggs/incubate/{egg_id}")
async def incubate_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if e["id"] == egg_id), None)
    if not egg:
        raise HTTPException(status_code=404, detail="Egg not found")
        
    if egg.get("status") != "fresh":
        raise HTTPException(status_code=400, detail="Egg already incubating or hatched")
        
    tier_info = EGG_TIERS.get(egg.get("tier", "common"), {"wait_min": 30})
    wait_min = tier_info["wait_min"]
    
    pets = user.get("pets", [DEFAULT_PET])
    active_pet = next((p for p in pets if p["name"] == user.get("current_pet")), {})
    if active_pet.get("ability") == "Caregiver":
        wait_min = int(wait_min * 0.5)
        
    ready_time = datetime.now() + timedelta(minutes=wait_min)
    
    uid_int = user["id"]
    if isinstance(uid_int, list): uid_int = uid_int[0]
    
    q = get_user_id_query(uid_int)
    q["eggs.id"] = egg_id
    await user_collection.update_one(
        q,
        {
            "$set": {
                "eggs.$.status": "incubating",
                "eggs.$.hatch_time": ready_time
            }
        }
    )
    return {"status": "success", "ready_at": ready_time.isoformat(), "wait_min": wait_min}

@router.post("/eggs/hatch/{egg_id}")
async def hatch_egg(egg_id: str, user: dict = Depends(get_current_user_data)):
    from Grabber.modules.economy.hunt import process_egg_hatch

    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if e["id"] == egg_id), None)
    
    if not egg or egg.get("status") != "incubating":
         raise HTTPException(status_code=400, detail="Egg not ready or not found")
         
    h_time = egg.get("hatch_time")
    if h_time and datetime.now() < h_time:
        raise HTTPException(status_code=400, detail="Egg still incubating")
        
    uid_int = user["id"]
    if isinstance(uid_int, list): uid_int = uid_int[0]

    success, result = await process_egg_hatch(uid_int, egg)
    
    if not success:
         msg = result.replace("<b>", "").replace("</b>", "").replace("💥 ", "").replace("⚠️ ", "").replace("\n", " ")
         status_code = "exploded" if "exploded" in result else "error"
         return {"status": status_code, "message": msg}
         
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
