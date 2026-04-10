from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from Grabber.webapp.auth import get_current_user, get_current_user_data, _user_locks
from Grabber.database import user_collection, collection
from Grabber.webapp.models import PaginatedResponse
from Grabber.core.constants import PAYOUTS
from Grabber.core.utils import normalize_user_id

router = APIRouter()

from Grabber.webapp.utils import get_user_id_query

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

    RARITY_SORT_ORDER = {
        "⚪ Common": 0,
        "🟢 Medium": 1,
        "🟠 Rare": 2,
        "🟡 Legendary": 3,
        "💠 Cosmic": 4,
        "💮 Exclusive": 5,
        "🔮 Limited Edition": 6,
        "🫧 Royal": 7,
        "💎 Antique": 8,
        "🎐 Celestial": 9,
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

    cursor = user_collection.aggregate(pipeline)
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
    uid_str = str(user_id)
    async with await _user_locks.get(uid_str):
        # Fetch fresh data under lock
        user = await user_collection.find_one(get_user_id_query(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        owned_chars = user.get("characters", [])
        if not owned_chars:
            raise HTTPException(status_code=400, detail="Harem is empty")
            
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
                
        # Resolve exact user id integer for mongo query compatibility
        uid_int = normalize_user_id(user["id"])

        removed_count = len(owned_chars) - len(new_harem)
        await user_collection.update_one(
            get_user_id_query(uid_int),
            {
                "$set": {"characters": new_harem},
                "$inc": {
                    "zenith": total_reward,
                    "char_count": -removed_count
                },
                # FIX: Prevent char_count from going negative if it was previously
                # desynchronised. $max floors the field at 0 after the decrement.
                "$max": {"char_count": 0}
            }
        )
        
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
        search = search.strip()
        match_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"anime": {"$regex": search, "$options": "i"}}
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
    result = await collection.aggregate(pipeline).to_list(length=1)
    total = result[0]["metadata"][0]["total"] if result and result[0].get("metadata") else 0
    items = result[0]["data"] if result else []

    # FIX: Use the already-fetched user doc from get_current_user_data.
    # The previous code issued a second find_one to get character IDs,
    # wasting a full DB round-trip on every gallery page load.
    owned_ids = set(c.get("id") for c in (user.get("characters") or []))

    for item in items:
        item["_id"] = str(item["_id"])
        item["owned"] = item.get("id") in owned_ids

    return {"total": total, "page": page, "items": items}
