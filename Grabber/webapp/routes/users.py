import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from config import config
from Grabber import LOGGER
from Grabber.webapp.auth import get_current_user, get_current_user_data, r
from Grabber.database import user_collection
from Grabber.webapp.models import UserProfileResponse
from Grabber.core.progression import get_user_progress, get_level_from_xp
from Grabber.core.cache import get_user_rank, get_total_ranked_users, update_user_rank, rebuild_leaderboard
from Grabber.core.utils import normalize_user_id
from Grabber.modules.progression.pet import DEFAULT_PET
import json

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

@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: dict = Depends(get_current_user_data)):
    user_id = normalize_user_id(user["id"])

    # Compute rank via Redis ZSET for O(log N) performance
    user_xp = user.get("xp", 0)
    rank = await get_user_rank(user_id)
    total_users = await get_total_ranked_users()
    
    if rank is None or total_users == 0:
        LOGGER.info(f"Leaderboard ZSET miss for {user_id}, falling back to Mongo.")
        rank = await user_collection.count_documents({"xp": {"$gt": user_xp}}) + 1
        total_users = await user_collection.count_documents({})
        await update_user_rank(user_id, user_xp)
        if total_users > 0 and (await get_total_ranked_users()) == 0:
            asyncio.create_task(rebuild_leaderboard(user_collection))

    percentile = round((1 - (rank / max(total_users, 1))) * 100, 1)
    
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
    clean_titles = [re.sub(r'[^\x00-\x7F]+', '', str(t or "")).strip() for t in titles_list]
    current_title = re.sub(r'[^\x00-\x7F]+', '', str(user.get("title") or "Rookie")).strip()
    
    progress = await get_user_progress(user_id, user_data=user)
    
    # Calculate total characters dynamically 
    # instead of aggregate $size since we already have the memory object
    total_characters = len(user.get("characters") or [])
    
    resp_data = {
        "id": int(user_id),
        "first_name": (user.get("first_name") or "User"),
        "username": user.get("username"),
        "avatar": user.get("avatar"),
        "stats": {
            "level": progress["level"],
            "xp": progress["xp"],
            "xp_needed": max(progress["xp_needed"], 1),
            "xp_current": min(progress["xp_current"], progress["xp_needed"]),
            "streak": user.get("streak", 0),
            "points": user.get("balance", 0),
            "zenith": user.get("zenith", 0),
            "badges": user.get("badges") or [],
            "total_characters": total_characters,
            "rank": rank,
            "percentile": percentile
        },
        "achievements": enriched_achievements,
        "titles": {
            "current": current_title,
            "all": clean_titles
        },
        "current_pet": None,
        "owned_pets": [],
        "eggs": []
    }

    # Handle Pets
    user_pets = user.get("pets", [DEFAULT_PET])
    current_pet_name = user.get("current_pet", DEFAULT_PET["name"])
    
    formatted_pets = []
    for p in user_pets:
        p_data = {
            "name": p["name"],
            "level": p.get("level", 1),
            "xp": p.get("xp", 0),
            "xp_needed": p.get("level", 1) * 100,
            "hp": p.get("hp", 100),
            "atk": p.get("atk", 10),
            "spd": p.get("spd", 10),
            "luck": p.get("luck", 0.1),
            "ability": p.get("ability", "None"),
            "desc": p.get("desc", ""),
            "img": p.get("img", ""),
            "is_active": p["name"] == current_pet_name
        }
        formatted_pets.append(p_data)
        if p_data["is_active"]:
            resp_data["current_pet"] = p_data

    resp_data["owned_pets"] = formatted_pets

    # Handle Eggs
    eggs = user.get("eggs", [])
    from datetime import datetime
    processed_eggs = []
    for egg in eggs:
        if isinstance(egg, str):
            # Resolve numeric or string tier to a cleaner name for the WebApp
            from Grabber.modules.economy.hunt import TIER_MAP
            tier_key = TIER_MAP.get(egg, egg)
            processed_eggs.append({
                "id": f"mig_{int(datetime.now().timestamp())}",
                "tier": tier_key,
                "name": f"{tier_key.capitalize()} Egg",
                "status": "fresh",
                "is_corrupted": False,
                "hatch_time": None,
                "remaining_mins": 0
            })
            continue

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
async def get_profile_legacy(user: dict = Depends(get_current_user_data)):
    """Backward compatibility for old client versions."""
    return await get_me(user)

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
    for i, u in enumerate(users, 1):
        processed = {
            "rank": i,
            "id": u.get("id"),
            "name": u.get("first_name", "User"),
            "value": u.get(field, 0),
            "avatar": u.get("avatar") 
        }
        if metric == "level":
            processed["level"] = get_level_from_xp(processed["value"])
        response_data.append(processed)
        
    if r:
        await r.setex(cache_key, 300, json.dumps(response_data))
    return response_data

@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user_data)):
    user_id = normalize_user_id(user["id"])
    user_xp = user.get("xp", 0)
    
    rank = await get_user_rank(user_id)
    total_users = await get_total_ranked_users()
    
    if rank is None or total_users == 0:
        LOGGER.info(f"Stats Leaderboard ZSET miss for {user_id}, falling back to Mongo.")
        rank = await user_collection.count_documents({"xp": {"$gt": user_xp}}) + 1
        total_users = await user_collection.count_documents({})
        await update_user_rank(user_id, user_xp)
        if total_users > 0 and (await get_total_ranked_users()) == 0:
            asyncio.create_task(rebuild_leaderboard(user_collection))

    percentile = (1 - (rank / max(total_users, 1))) * 100
    
    return {
        "rank": rank,
        "percentile": round(percentile, 2),
        "total_games": user.get("total_games", 0),
        "win_rate": user.get("win_rate", 0),
        "total_captured": len(user.get("characters", []))
    }
