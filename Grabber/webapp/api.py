from fastapi import APIRouter, Depends, HTTPException, Query
from Grabber.webapp.auth import get_current_user
from Grabber.database import user_collection, client, db
from Grabber.core.progression import get_user_progress, get_level_from_xp
from Grabber.webapp.models import UserProfileResponse, PaginatedResponse, QuestsResponse, StatsModel, TitlesModel
from typing import Optional
import json
import logging
from Grabber.webapp.auth import r
from config import config
import re
from datetime import datetime, timedelta
from Grabber.modules.progression.pet import DEFAULT_PET, PET_SHOP
from Grabber.modules.economy.hunt import EGG_TIERS, process_egg_hatch
from Grabber.modules.progression.battlepass import PASS_PRICES, LEVEL_REWARDS, PASS_EMOJI
from Grabber.modules.economy.shop import get_daily_shop_characters, SHOP_LIMIT, DEFAULT_ZENITH_PRICE, SHOP_RARITY

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
async def get_rarities(user_id: int = Depends(get_current_user)):
    """Fetch distinct rarities from the database character collection."""
    from Grabber.database import collection
    rarities = await collection.distinct("rarity")
    # Filter out None and sort if possible
    rarities = [r for r in rarities if r]
    return sorted(rarities)

@router.get("/character/{char_id}")
async def get_character(char_id: str, user_id: int = Depends(get_current_user)):
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

    # Compute rank (run concurrently with other data)
    total_users = await user_collection.count_documents({})
    user_xp = user.get("xp", 0)
    rank = await user_collection.count_documents({"xp": {"$gt": user_xp}}) + 1
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
    # Remove emojis from titles for WebApp
    clean_titles = [re.sub(r'[^\x00-\x7F]+', '', str(t or "")).strip() for t in titles_list]
    current_title = re.sub(r'[^\x00-\x7F]+', '', str(user.get("title") or "Rookie")).strip()
    # Performance: Pass existing user document to avoid redundant DB lookup
    progress = await get_user_progress(user_id, user_data=user)
    
    resp_data = {
        "id": user_id,
        "first_name": (user.get("first_name") or "User"),
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
            "total_characters": user.get("total_characters", 0),
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
    search: Optional[str] = None,
    rarity: Optional[str] = None
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
    search: Optional[str] = None,
    rarity: Optional[str] = None,
    user_id: int = Depends(get_current_user)
):
    from Grabber.database import collection
    match_query = {}
    if search:
        search = search.strip()
        match_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"anime": {"$regex": search, "$options": "i"}}
        ]
    if rarity:
        match_query["rarity"] = rarity.strip()

    # Use $facet to get count + paginated data in a single DB round-trip (#11 fix)
    skip = (page - 1) * limit
    pipeline = [
        {"$match": match_query},
        {"$facet": {
            "metadata": [{"$count": "total"}],
            "data": [{"$skip": skip}, {"$limit": limit}]
        }}
    ]
    result = await collection.aggregate(pipeline).to_list(length=1)
    total = result[0]["metadata"][0]["total"] if result and result[0].get("metadata") else 0
    items = result[0]["data"] if result else []

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
    if not user:  # Fix #8: missing null guard
        raise HTTPException(status_code=404, detail="User not found")
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

# --- SHOP ENDPOINTS ---

@router.get("/shop/hub")
async def get_shop_hub(user_id: int = Depends(get_current_user)):
    """General shop status and user balances."""
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})  # Fix #7
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "balance": user.get("balance", 0),
        "zenith": user.get("zenith", 0),
        "pass_type": user.get("pass_type", "free"),
        "characters_rarity": SHOP_RARITY
    }

@router.get("/shop/characters")
async def get_shop_characters(user_id: int = Depends(get_current_user)):
    """Fetch daily character stock."""
    chars = await get_daily_shop_characters()
    # Check "Owned" status
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}}, {"characters.id": 1})  # Fix #7
    owned_ids = set(c.get("id") for c in (user.get("characters") or [])) if user else set()
    
    response = []
    for c in chars:
        char_dict = c.dict()
        char_dict["owned"] = c.id in owned_ids
        char_dict["stock_limit"] = SHOP_LIMIT
        response.append(char_dict)
    return response

@router.post("/shop/buy/character/{char_id}")
async def buy_character_api(char_id: str, user_id: int = Depends(get_current_user)):
    """Logic mirror from modules/economy/shop.py but returning JSON errors."""
    from Grabber.database import collection
    from Grabber.modules.progression.quests import update_quest_progress
    from Grabber.modules.progression.achievements import check_achievements

    user_raw = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})  # Fix #7
    if not user_raw: raise HTTPException(status_code=404, detail="User not found")
    
    char_raw = await collection.find_one({"id": char_id})
    if not char_raw or char_raw.get("rarity") != SHOP_RARITY:
        raise HTTPException(status_code=404, detail="Character not available in shop")
    
    price = char_raw.get("zenith_price", DEFAULT_ZENITH_PRICE)
    if user_raw.get("zenith", 0) < price:
        raise HTTPException(status_code=400, detail=f"Insufficient Zenith (Need {price})")
        
    # Ownership Check
    owned_ids = [c["id"] for c in user_raw.get("characters", []) if isinstance(c, dict) and "id" in c]
    if char_id in owned_ids:
        raise HTTPException(status_code=400, detail="You already own this character")

    # Atomic Update for Global Stock
    stock_update = await collection.update_one(
        {"id": char_id, "sold_count": {"$lt": SHOP_LIMIT}},
        {"$inc": {"sold_count": 1}}
    )
    if stock_update.modified_count == 0:
        raise HTTPException(status_code=400, detail="Character is SOLD OUT")

    # User Update
    user_update = await user_collection.update_one(
        {"id": user_id, "zenith": {"$gte": price}},
        {
            "$inc": {"zenith": -price},
            "$push": {"characters": {
                "id": char_raw["id"], 
                "name": char_raw["name"], 
                "anime": char_raw["anime"], 
                "rarity": char_raw["rarity"], 
                "img_url": char_raw["img_url"]
            }}
        }
    )

    if user_update.modified_count == 0:
        await collection.update_one({"id": char_id}, {"$inc": {"sold_count": -1}}) # Rollback
        raise HTTPException(status_code=500, detail="Transaction failed")

    await update_quest_progress(user_id, "big_spender", price)
    await check_achievements(user_id)
    return {"status": "success", "char_name": char_raw["name"]}

@router.get("/shop/pets")
async def get_shop_pets(user_id: int = Depends(get_current_user)):
    """Fetch potential pets and ownership status."""
    user = await user_collection.find_one({"id": {"$in": [user_id, str(user_id)]}})  # Fix #7
    owned_pet_names = [p["name"] for p in user.get("pets", [])] if user else []
    
    return {
        "pets": PET_SHOP,
        "owned": owned_pet_names,
        "current_level": (await get_user_progress(user_id))["level"]
    }

@router.post("/shop/buy/pet/{pet_index}")
async def buy_pet_api(pet_index: int, user_id: int = Depends(get_current_user)):
    from Grabber.modules.progression.pet import perform_pet_purchase
    result = await perform_pet_purchase(user_id, pet_index)
    if result is True:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail=str(result).replace("❌ ", "").replace("🔒 ", ""))

@router.get("/shop/battlepass")
async def get_battlepass_shop(user_id: int = Depends(get_current_user)):
    progress = await get_user_progress(user_id)
    return {
        "prices": PASS_PRICES,
        "current_tier": progress["pass_type"],
        "level": progress["level"]
    }

@router.post("/shop/upgrade_pass/{tier}")
async def upgrade_pass_api(tier: str, user_id: int = Depends(get_current_user)):
    if tier not in PASS_PRICES: raise HTTPException(status_code=400, detail="Invalid tier")
    
    user = await user_collection.find_one({"id": user_id})
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    current_tier = user.get("pass_type", "free")
    tiers_order = ["free", "premium", "elite"]
    if tiers_order.index(current_tier) >= tiers_order.index(tier):
        raise HTTPException(status_code=400, detail="You already have this tier or higher")
        
    price = PASS_PRICES[tier]
    if user.get("zenith", 0) < price:
        raise HTTPException(status_code=400, detail=f"Insufficient Zenith (Need {price})")
        
    await user_collection.update_one(
        {"id": user_id, "zenith": {"$gte": price}},
        {"$set": {"pass_type": tier}, "$inc": {"zenith": -price}}
    )
    return {"status": "success", "new_tier": tier}
