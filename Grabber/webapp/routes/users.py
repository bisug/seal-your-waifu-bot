import asyncio
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from config import config
from Grabber import LOGGER
from Grabber.core.progression import get_level_from_xp, get_user_progress
from Grabber.core.tasks import run_background_task
from Grabber.core.user import get_user_rank_with_fallback
from Grabber.core.utils import get_user_id_query, normalize_user_id
from Grabber.database import user_collection
from Grabber.modules.economy.hunt import EGG_TIERS, TIER_MAP
from Grabber.modules.progression.achievements import ACHIEVEMENTS
from Grabber.modules.progression.pet import (DEFAULT_PET,
                                             get_effective_affection)
from Grabber.webapp.auth import get_current_user, get_current_user_data, r
from Grabber.webapp.schemas import UserProfileResponse

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

@router.get("/achievements/list")
async def get_achievements_list(user_id: int = Depends(get_current_user)):
    """Return all possible achievements and whether the user has them."""
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_achievements = set(user.get("achievements") or [])

    all_achievements = []
    for ach_id, data in ACHIEVEMENTS.items():
        all_achievements.append({
            "id": ach_id,
            "name": data["name"],
            "description": data["description"],
            "icon": data.get("symbol", "✦"),
            "reward_xp": data.get("reward_xp", 0),
            "unlocked": ach_id in user_achievements
        })

    return all_achievements

@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: dict = Depends(get_current_user_data)):
    user_id = normalize_user_id(user["id"])

    user_xp = user.get("xp", 0)
    rank, total_users, percentile = await get_user_rank_with_fallback(user_id, user_xp)

    
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
    # using denormalized char_count
    total_characters = user.get("char_count")
    if total_characters is None:
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
        "pets": [],
        "eggs": []
    }

    # Handle Pets
    user_pets = user.get("pets", [DEFAULT_PET])
    current_pet_name = user.get("current_pet", DEFAULT_PET["name"])
    
    formatted_pets = []
    for p in user_pets:
        eff_affection = get_effective_affection(p)
        if eff_affection >= 80:
            mood = "🥰 Happy"
        elif eff_affection <= 20:
            mood = "😢 Sad"
        else:
            mood = "😐 Neutral"
            
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
            "affection": eff_affection,
            "mood": mood,
            "is_active": p["name"] == current_pet_name
        }
        formatted_pets.append(p_data)
        if p_data["is_active"]:
            resp_data["current_pet"] = p_data

    resp_data["pets"] = formatted_pets

    # Handle Eggs
    eggs = user.get("eggs", [])
    processed_eggs = []
    migration_needed = False
    for idx, egg in enumerate(eggs):
        if isinstance(egg, str):
            migration_needed = True
            tier_key = TIER_MAP.get(egg, egg)
            stable_id = str(uuid.uuid4())[:12]
            processed_eggs.append({
                "id": f"mig_{stable_id}",
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
    
    if migration_needed:
        from Grabber.core.utils import get_user_id_query
        db_eggs = [{k: v for k, v in e.items() if k != "remaining_mins"} for e in processed_eggs]
        run_background_task(user_collection.update_one(
            get_user_id_query(int(user_id)),
            {"$set": {"eggs": db_eggs}}
        ))
    
    return resp_data


@router.get("/profile", include_in_schema=False)
async def get_profile_legacy():
    """Backward compatibility for old client versions."""
    return RedirectResponse(url="./me", status_code=307)

@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("harem", pattern="^(harem|shards|zenith|level|guesses)$"),
    limit: int = Query(50, ge=1, le=100)
):
    from Grabber.modules.info.leaderboard import METRICS, get_top_users
    users = await get_top_users(metric, limit)
    
    field = METRICS[metric]["field"]
    response_data = []
    for i, u in enumerate(users, 1):
        first_name = u.get("first_name", "User")
        last_name = u.get("last_name")
        full_name = f"{first_name} {last_name}" if last_name else first_name

        processed = {
            "rank": i,
            "id": u.get("id"),
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "username": u.get("username"),
            "value": u.get(field, 0),
            "avatar": u.get("avatar") 
        }
        if metric == "level":
            processed["level"] = get_level_from_xp(processed["value"])
        response_data.append(processed)
        
    return response_data

@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user_data)):
    user_id = normalize_user_id(user["id"])
    user_xp = user.get("xp", 0)
    rank, total_users, percentile = await get_user_rank_with_fallback(user_id, user_xp)

    
    return {
        "rank": rank,
        "percentile": round(percentile, 2),
        "total_games": user.get("total_games", 0),
        "win_rate": user.get("win_rate", 0),
        "total_captured": user.get("char_count") or len(user.get("characters", []))
    }
