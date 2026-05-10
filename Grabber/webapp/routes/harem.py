import re
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from Grabber import LOGGER
from Grabber.core.cache import sync_user_to_redis
from Grabber.core.constants import PAYOUTS
from Grabber.core.utils import get_user_id_query, normalize_user_id
from Grabber.database import collection, user_collection
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.webapp.schemas import PaginatedResponse

router = APIRouter()


@router.get("/rarities")
async def get_rarities(user_id: int = Depends(get_current_user)):
    rarities = await collection.distinct("rarity")
    rarities = [r for r in rarities if r]
    return sorted(rarities)

@router.get("/character/{char_id}")
async def get_character(char_id: str, user_id: int = Depends(get_current_user)):
    char = await collection.find_one({"id": char_id})
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    char["_id"] = str(char["_id"])
    return char

@router.get("/harem", response_model=PaginatedResponse)
async def get_harem(
    user_id: int = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    search: Optional[str] = None,
    rarity: Optional[str] = None
):
    pipeline = [
        {"$match": get_user_id_query(user_id)},
        {"$unwind": "$characters"}
    ]

    if search:
        search = search.strip()
        search_regex = {"$regex": re.escape(search), "$options": "i"}
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

    RARITY_SORT_ORDER = {
        "⚪ Common": 10,
        "🟢 Medium": 9,
        "🟠 Rare": 8,
        "🟡 Legendary": 7,
        "💠 Cosmic": 6,
        "💮 Exclusive": 5,
        "🔮 Limited Edition": 4,
        "🫧 Royal": 3,
        "💎 Antique": 2,
        "🎐 Celestial": 1,
        "🎞️ AMV": 0,
        "🪽 Prestige": -1
    }

    pipeline.extend([
        {"$group": {
            "_id": "$characters.id",
            "doc": {"$first": "$characters"},
            "count": {"$sum": 1}
        }},
        {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"count": "$count"}]}}},
        {"$addFields": {
            "_rarity_order": {"$switch": {
                "branches": [
                    {"case": {"$eq": ["$rarity", k]}, "then": v}
                    for k, v in RARITY_SORT_ORDER.items()
                ],
                "default": 99
            }}
        }},
        {"$sort": {"_rarity_order": 1, "name": 1}}
    ])

    skip = (page - 1) * limit
    facet = {
        "metadata": [{"$count": "total"}],
        "data": [{"$skip": skip}, {"$limit": limit}]
    }
    pipeline.append({"$facet": facet})

    cursor = await user_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    total = 0
    paginated = []
    if result and result[0].get("metadata"):
        total = result[0]["metadata"][0]["total"]
        paginated = result[0]["data"]

    return {"total": total, "page": page, "items": paginated}

@router.post("/recycle")
async def recycle_characters(
    char_ids: List[str] = Body(...), 
    user_id: int = Depends(get_current_user)
):
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    owned_chars = user.get("characters", [])
    if not owned_chars:
        raise HTTPException(status_code=400, detail="Harem is empty")

    stored_char_count = user.get("char_count", len(owned_chars))
    original_harem_len = len(owned_chars)
        
    from collections import Counter
    to_recycle_counts = Counter(char_ids)
    
    total_reward = 0
    current_counts = Counter(c["id"] for c in owned_chars)
    
    for rid, rcount in to_recycle_counts.items():
        if current_counts[rid] < rcount:
             raise HTTPException(status_code=400, detail=f"Insufficient duplicates for ID {rid}")
             
    new_harem = []
    temp_counts = Counter(to_recycle_counts)
    
    for char in owned_chars:
        cid = char["id"]
        if temp_counts[cid] > 0:
            rarity = char.get("rarity", "⚪ Common")
            total_reward += PAYOUTS.get(rarity, 10)
            temp_counts[cid] -= 1
        else:
            new_harem.append(char)
            
    uid_int = normalize_user_id(user["id"])
    removed_count = len(owned_chars) - len(new_harem)
    new_char_count = max(0, stored_char_count - removed_count)
    
    # OCC: Ensure user hasn't modified harem since load
    current_version = user.get("version", 0)
    q = {**get_user_id_query(uid_int), "version": current_version}
    
    res = await user_collection.update_one(
        q,
        {
            "$set": {"characters": new_harem, "char_count": new_char_count},
            "$inc": {"zenith": total_reward, "version": 1}
        }
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=409, detail="User data modified during transaction. Please try again.")
    
    await sync_user_to_redis(user_id)
    return {"status": "success", "reward": total_reward, "count": len(char_ids)}

@router.get("/gallery", response_model=PaginatedResponse)
async def get_gallery(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=50),
    search: Optional[str] = None,
    rarity: Optional[str] = None,
    user: dict = Depends(get_current_user_data)
):
    match_query = {}
    if search:
        search_escaped = re.escape(search.strip())
        match_query["$or"] = [
            {"name": {"$regex": search_escaped, "$options": "i"}},
            {"anime": {"$regex": search_escaped, "$options": "i"}}
        ]
    if rarity:
        match_query["rarity"] = rarity.strip()

    skip = (page - 1) * limit
    pipeline = [
        {"$match": match_query},
        {"$facet": {
            "metadata": [{"$count": "total"}],
            "data": [{"$skip": skip}, {"$limit": limit}]
        }}
    ]
    cursor = await collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    total = result[0]["metadata"][0]["total"] if result and result[0].get("metadata") else 0
    items = result[0]["data"] if result else []

    # Optimization: Use user doc from get_current_user_data to avoid redundant DB call
    owned_ids = set(c.get("id") for c in (user.get("characters") or []))

    for item in items:
        item["_id"] = str(item["_id"])
        item["owned"] = item.get("id") in owned_ids

    return {"total": total, "page": page, "items": items}
