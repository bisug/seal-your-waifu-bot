from fastapi import APIRouter, Depends, HTTPException, Query
from Grabber.webapp.auth import get_current_user
from Grabber.database import user_collection, client, db
from Grabber.core.progression import get_user_progress, get_level_from_xp
from Grabber.webapp.models import UserProfileResponse, PaginatedResponse, QuestsResponse, StatsModel, TitlesModel
import json
import logging
from Grabber.webapp.auth import r
from config import config
import re
from datetime import datetime, timedelta
from Grabber.modules.progression.pet import DEFAULT_PET, PET_SHOP
from Grabber.modules.economy.hunt import EGG_TIERS

router = APIRouter()

@router.get("/bot/info")
async def get_bot_info():
    """Public endpoint to get bot identity for branding."""
    return {
        "name": getattr(config, "BOT_NAME", "SEAL YOUR WAIFU"),
        "username": getattr(config, "BOT_USERNAME", "Seal_Your_WaifuBot"),
        "id": getattr(config, "BOT_ID", None),
        "avatar": config.PHOTO_URL[0] if config.PHOTO_URL else "https://files.catbox.moe/2hsawz.jpg"
    }

@router.get("/rarities")
async def get_rarities():
    """Fetch distinct rarities from the database character collection."""
    from Grabber.database import collection
    rarities = await collection.distinct("rarity")
    # Filter out None and sort if possible
    rarities = [r for r in rarities if r]
    return sorted(rarities)

@router.get("/character/{char_id}")
async def get_character(char_id: str):
    """Fetch details for a specific character."""
    from Grabber.database import collection
    char = await collection.find_one({"id": char_id})
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    char["_id"] = str(char["_id"])
    return char

@router.get("/me", response_model=UserProfileResponse)
async def get_me(user_id: int = Depends(get_current_user)):
    pipeline = [
        {"$match": {"id": {"$in": [user_id, str(user_id)]}}},
        {"$project": {
            "id": 1, "first_name": 1, "username": 1, "avatar": 1, "level": 1, "xp": 1,
            "streak": 1, "balance": 1, "zenith": 1, "badges": 1, "achievements": 1,
            "titles": 1, "title": 1, "pets": 1, "current_pet": 1, "eggs": 1,
            "total_characters": {"$size": {"$ifNull": ["$characters", []]}}
        }}
    ]
    cursor = user_collection.aggregate(pipeline)
    users = await cursor.to_list(length=1)
    user = users[0] if users else None

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from Grabber.modules.progression.achievements import ACHIEVEMENTS
    raw_achievements = user.get("achievements") or []
    enriched_achievements = []
    for ach_id in raw_achievements:
        if ach_id in ACHIEVEMENTS:
            enriched_achievements.append({
                "id": ach_id,
                "name": ACHIEVEMENTS[ach_id]["name"],
                "icon": ACHIEVEMENTS[ach_id].get("symbol", "✦")
            })

    titles_list = user.get("titles") or ["Rookie"]
    # Remove emojis from titles for WebApp
    clean_titles = [re.sub(r'[^\x00-\x7F]+', '', t).strip() for t in titles_list]
    current_title = re.sub(r'[^\x00-\x7F]+', '', user.get("title", "Rookie")).strip()
    # Performance: Pass existing user document to avoid redundant DB lookup
    progress = await get_user_progress(user_id, user_data=user)
    
    resp_data = {
        "id": user_id,
        "first_name": user.get("first_name", "User"),
        "username": user.get("username"),
        "avatar": user.get("avatar"),
        "stats": {
            "level": progress["level"],
            "xp": progress["xp"],
            "xp_current": progress["xp_current"],
            "xp_needed": progress["xp_needed"],
            "streak": user.get("streak", 0),
            "points": user.get("balance", 0),
            "zenith": user.get("zenith", 0),
            "badges": user.get("badges") or [],
            "total_characters": user.get("total_characters", 0)
        },
        "achievements": enriched_achievements,
        "titles": {
            "current": current_title,
            "all": clean_titles
        },
        "current_pet": None,
        "eggs": []
    }

    # Handle Pet
    user_pets = user.get("pets", [DEFAULT_PET])
    current_pet_name = user.get("current_pet", DEFAULT_PET["name"])
    pet_data = next((p for p in user_pets if p["name"] == current_pet_name), DEFAULT_PET)
    
    if pet_data:
        resp_data["current_pet"] = {
            "name": pet_data["name"],
            "level": pet_data.get("level", 1),
            "xp": pet_data.get("xp", 0),
            "xp_needed": pet_data.get("level", 1) * 100,
            "hp": pet_data.get("hp", 100),
            "atk": pet_data.get("atk", 10),
            "spd": pet_data.get("spd", 10),
            "luck": pet_data.get("luck", 0.1),
            "ability": pet_data.get("ability", "None"),
            "desc": pet_data.get("desc", ""),
            "img": pet_data.get("img", ""),
            "is_active": True
        }

    # Handle Eggs
    eggs = user.get("eggs", [])
    processed_eggs = []
    for egg in eggs:
        h_time = egg.get("hatch_time")
        rem_mins = 0
        if h_time and isinstance(h_time, datetime):
            if datetime.now() < h_time:
                rem_mins = int((h_time - datetime.now()).total_seconds() / 60)
            h_time = h_time.isoformat()
        
        processed_eggs.append({
            "id": egg.get("id"),
            "tier": egg.get("tier", "common"),
            "name": egg.get("name", "Unknown Egg"),
            "status": egg.get("status", "fresh"),
            "is_corrupted": egg.get("is_corrupted", False),
            "hatch_time": h_time,
            "remaining_mins": rem_mins
        })
    resp_data["eggs"] = processed_eggs
    
    return resp_data

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile_legacy(user_id: int = Depends(get_current_user)):
    """Backward compatibility for old client versions."""
    return await get_me(user_id)

@router.get("/harem", response_model=PaginatedResponse)
async def get_harem(
    user_id: int = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    search: str = None,
    rarity: str = None
):
    # MongoDB Aggregation Pipeline for Harem
    pipeline = [
        {"$match": {"id": {"$in": [user_id, str(user_id)]}}},
        {"$unwind": "$characters"}
    ]

    # Filtering
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        pipeline.append({
            "$match": {
                "$or": [
                    {"characters.name": search_regex},
                    {"characters.anime": search_regex}
                ]
            }
        })
        
    if rarity:
        pipeline.append({
            "$match": {"characters.rarity": rarity}
        })

    # Grouping to count duplicates and formatting the document
    pipeline.extend([
        {"$group": {
            "_id": "$characters.id",
            "doc": {"$first": "$characters"},
            "count": {"$sum": 1}
        }},
        {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"count": "$count"}]}}},
        {"$sort": {"rarity": 1, "name": 1}} # Example sorting
    ])

    # Pagination Facet
    skip = (page - 1) * limit
    facet = {
        "metadata": [{"$count": "total"}],
        "data": [{"$skip": skip}, {"$limit": limit}]
    }
    pipeline.append({"$facet": facet})

    cursor = user_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    total = 0
    paginated = []
    if result and result[0].get("metadata"):
        total = result[0]["metadata"][0]["total"]
        paginated = result[0]["data"]

    return {
        "total": total,
        "page": page,
        "items": paginated
    }

@router.get("/gallery", response_model=PaginatedResponse)
async def get_gallery(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=50),
    search: str = None,
    rarity: str = None,
    user_id: int = Depends(get_current_user)
):
    from Grabber.database import collection
    query = {}
    if search:
        search = search.strip()
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"anime": {"$regex": search, "$options": "i"}}
        ]
    if rarity:
        rarity = rarity.strip()
        query["rarity"] = rarity
        
    cursor = collection.find(query).skip((page - 1) * limit).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await collection.count_documents(query)
    
    # Check "Owned" status - ONLY fetch the IDs to save memory
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}}, {"characters.id": 1})
    owned_ids = set(c.get("id") for c in (user.get("characters") or [])) if user else set()
    
    for item in items:
        item["_id"] = str(item["_id"])
        item["owned"] = item.get("id") in owned_ids
        
    return {
        "total": total,
        "page": page,
        "items": items
    }

@router.get("/quests", response_model=QuestsResponse)
async def get_quests(user_id: int = Depends(get_current_user)):
    from Grabber.modules.progression.quests import get_user_quests, QUEST_POOL, WEEKLY_POOL
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
    from Grabber.modules.progression.quests import get_user_quests, QUEST_POOL, WEEKLY_POOL, add_xp
    
    quests = await get_user_quests(user_id)
    if quest_id not in quests:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    qdata = quests[quest_id]
    if qdata.get("claimed"):
        raise HTTPException(status_code=400, detail="Already claimed")
        
    info = QUEST_POOL.get(quest_id) or WEEKLY_POOL.get(quest_id)
    if qdata.get("progress", 0) < info["target"]:
        raise HTTPException(status_code=400, detail="Quest not completed")
        
    # Logic mirror from modules/quests.py
    await add_xp(user_id, info["reward_xp"], f"quest_{quest_id}")
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {f"quests.{quest_id}.claimed": True}}
    )
    
    return {"success": True, "reward_xp": info["reward_xp"]}

@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("harem", pattern="^(harem|shards|zenith|level|guesses)$"),
    limit: int = Query(50, ge=1, le=100)
):
    cache_key = f"leaderboard:{metric}:{limit}"
    cached = await r.get(cache_key) if r else None
    if cached:
        return json.loads(cached)
        
    from Grabber.modules.info.leaderboard import get_top_users
    users = await get_top_users(metric, limit)
    
    metric_map = {
        "harem": "char_count",
        "shards": "balance",
        "zenith": "zenith",
        "level": "xp",
        "guesses": "guess_count"
    }
    field = metric_map.get(metric, "xp")
    
    response_data = []
    for i, user in enumerate(users, 1):
        processed = {
            "rank": i,
            "id": user.get("id"),
            "name": user.get("first_name", "User"),
            "value": user.get(field, 0),
            "avatar": user.get("avatar") # Support avatars in LB if available
        }
        if metric == "level":
            processed["level"] = get_level_from_xp(processed["value"])
        response_data.append(processed)
        
    if r:
        await r.setex(cache_key, 60, json.dumps(response_data))
    return response_data

@router.get("/stats")
async def get_stats(user_id: int = Depends(get_current_user)):
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    total_users = await user_collection.count_documents({})
    rank = await user_collection.count_documents({"xp": {"$gt": user.get("xp", 0)}}) + 1
    percentile = (1 - (rank / total_users)) * 100
    
    return {
        "rank": rank,
        "percentile": round(percentile, 2),
        "total_games": user.get("total_games", 0),
        "win_rate": user.get("win_rate", 0),
        "total_captured": len(user.get("characters", []))
    }
@router.post("/pets/set_active/{pet_name}")
async def set_active_pet(pet_name: str, user_id: int = Depends(get_current_user)):
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    pets = user.get("pets", [DEFAULT_PET])
    if not any(p["name"] == pet_name for p in pets):
        raise HTTPException(status_code=400, detail="Pet not owned")
        
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"current_pet": pet_name}}
    )
    return {"status": "success", "pet": pet_name}

@router.post("/eggs/incubate/{egg_id}")
async def incubate_egg(egg_id: str, user_id: int = Depends(get_current_user)):
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if e["id"] == egg_id), None)
    if not egg:
        raise HTTPException(status_code=404, detail="Egg not found")
        
    if egg.get("status") != "fresh":
        raise HTTPException(status_code=400, detail="Egg already incubating or hatched")
        
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    wait_min = tier_info["wait_min"]
    
    # Caregiver ability check
    pets = user.get("pets", [DEFAULT_PET])
    active_pet = next((p for p in pets if p["name"] == user.get("current_pet")), {})
    if active_pet.get("ability") == "Caregiver":
        wait_min = int(wait_min * 0.5)
        
    ready_time = datetime.now() + timedelta(minutes=wait_min)
    
    await user_collection.update_one(
        {"id": user_id, "eggs.id": egg_id},
        {
            "$set": {
                "eggs.$.status": "incubating",
                "eggs.$.hatch_time": ready_time
            }
        }
    )
    return {"status": "success", "ready_at": ready_time.isoformat(), "wait_min": wait_min}

@router.post("/eggs/hatch/{egg_id}")
async def hatch_egg(egg_id: str, user_id: int = Depends(get_current_user)):
    from Grabber.modules.economy.hunt import process_egg_hatch
    
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if e["id"] == egg_id), None)
    
    if not egg or egg.get("status") != "incubating":
         raise HTTPException(status_code=400, detail="Egg not ready or not found")
         
    h_time = egg.get("hatch_time")
    if h_time and datetime.now() < h_time:
        raise HTTPException(status_code=400, detail="Egg still incubating")
        
    success, result = await process_egg_hatch(user_id, egg)
    
    if not success:
         # Clean the HTML formatting out for the API JSON response
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
