from fastapi import APIRouter, Depends, HTTPException, Query
from Grabber.webapp.auth import get_current_user
from Grabber.database import user_collection, client, db
from Grabber.core.progression import get_user_progress, get_level_from_xp
from Grabber.webapp.models import UserProfileResponse, PaginatedResponse, QuestsResponse, StatsModel, TitlesModel
import json
import logging
from Grabber.webapp.auth import r
from config import config

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
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    achievements = user.get("achievements") or []
    titles_list = user.get("titles") or ["Rookie"]
    characters = user.get("characters") or []
    progress = await get_user_progress(user_id)
    
    return {
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
            "total_characters": len(characters)
        },
        "achievements": achievements,
        "titles": {
            "current": user.get("title", "Rookie"),
            "all": titles_list
        }
    }

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
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    chars = user.get("characters") or []
    
    # Filtering
    if search:
        chars = [c for c in chars if search.lower() in c.get("name", "").lower() or search.lower() in c.get("anime", "").lower()]
    if rarity:
        chars = [c for c in chars if c.get("rarity") == rarity]
        
    # Grouping and counting duplicates
    from collections import Counter
    char_counts = Counter(c.get("id") for c in chars)
    
    # Unique characters for listing
    unique_chars = []
    seen = set()
    for c in chars:
        cid = c.get("id")
        if cid not in seen:
            unique_chars.append(c)
            seen.add(cid)
            
    # Pagination
    total = len(unique_chars)
    start = (page - 1) * limit
    end = start + limit
    paginated = unique_chars[start:end]
    
    # Attach counts
    for c in paginated:
        c["count"] = char_counts[c.get("id")]
        
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
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"anime": {"$regex": search, "$options": "i"}}
        ]
    if rarity:
        query["rarity"] = rarity
        
    cursor = collection.find(query).skip((page - 1) * limit).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await collection.count_documents(query)
    
    # Check "Owned" status
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})
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
    from Grabber.modules.quests import get_user_quests, QUEST_POOL, WEEKLY_POOL
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
    from Grabber.modules.quests import get_user_quests, QUEST_POOL, WEEKLY_POOL, add_xp
    
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
    metric: str = Query("harem", regex="^(harem|shards|zenith|level|guesses)$"),
    limit: int = Query(50, ge=1, le=100)
):
    cache_key = f"leaderboard:{metric}:{limit}"
    cached = await r.get(cache_key) if r else None
    if cached:
        return json.loads(cached)
        
    from Grabber.modules.leaderboard import get_top_users
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
