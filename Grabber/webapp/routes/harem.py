import asyncio
import time
from collections import Counter
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from Grabber import LOGGER
from Grabber.core.cache import sync_user_to_redis
from Grabber.core.character_search import build_character_search_filter
from Grabber.modules.economy.sell import get_sell_price
from Grabber.core.utils import get_user_id_query, normalize_user_id
from Grabber.database import collection, user_collection
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.webapp.schemas import PaginatedResponse

router = APIRouter()
RARITY_CACHE_TTL = 300
_rarity_cache: dict[str, object] = {"expires_at": 0.0, "items": []}

# Short-lived cache for gallery totals: count_documents() with a search filter
# is a collection scan and runs on every paginated request otherwise.
GALLERY_COUNT_TTL = 60
_gallery_count_cache: dict[str, tuple[float, int]] = {}


async def _cached_gallery_count(match_query: dict) -> int:
    import json as _json
    cache_key = _json.dumps(match_query, sort_keys=True, default=str)
    now = time.monotonic()
    hit = _gallery_count_cache.get(cache_key)
    if hit and now - hit[0] < GALLERY_COUNT_TTL:
        return hit[1]
    total = await collection.count_documents(match_query)
    if len(_gallery_count_cache) > 200:
        _gallery_count_cache.clear()
    _gallery_count_cache[cache_key] = (now, total)
    return total


@router.get("/rarities")
async def get_rarities(user_id: int = Depends(get_current_user)):
    now = time.monotonic()
    if now < float(_rarity_cache["expires_at"]) and _rarity_cache["items"]:
        return _rarity_cache["items"]

    rarities = await collection.distinct("rarity")
    rarities = [r for r in rarities if r]
    sorted_rarities = sorted(rarities)
    _rarity_cache["items"] = sorted_rarities
    _rarity_cache["expires_at"] = now + RARITY_CACHE_TTL
    return sorted_rarities

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

    search_filter = build_character_search_filter(search, field_prefix="characters.")
    if search_filter:
        pipeline.append({"$match": search_filter})
        
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

@router.post("/recycle/preview")
async def recycle_preview(
    char_ids: List[str] = Body(...),
    user_id: int = Depends(get_current_user)
):
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    owned_chars = user.get("characters", [])
    current_counts = Counter(c["id"] for c in owned_chars)

    total_reward = 0
    char_map = {c["id"]: c for c in owned_chars}

    for rid in char_ids:
        if current_counts.get(rid, 0) > 0:
            char = char_map.get(rid)
            if char:
                rarity = char.get("rarity", "⚪ Common")
                total_reward += get_sell_price(rarity, user_id)
                current_counts[rid] -= 1
        else:
             raise HTTPException(status_code=400, detail=f"Character ID {rid} not owned or insufficient duplicates")

    return {"reward": total_reward, "count": len(char_ids)}

@router.post("/character/sell/{char_id}")
async def sell_character_api(
    char_id: str,
    user_id: int = Depends(get_current_user)
):
    from Grabber.modules.economy.sell import sell_character_from_user

    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    char = next((c for c in user.get("characters", []) if c["id"] == char_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found in harem")

    sale = await sell_character_from_user(user_id, char_id)
    if not sale:
        raise HTTPException(status_code=400, detail="Failed to sell character")
    _, price, _ = sale
    return {"status": "success", "reward": price, "currency": "Shards"}

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
            total_reward += get_sell_price(rarity, user_id)
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
            "$inc": {"balance": total_reward, "version": 1}
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
    sort: str = Query("numeric", pattern="^(numeric|alphabet)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    user_id: int = Depends(get_current_user)
):
    match_query = build_character_search_filter(search) or {}
    if rarity:
        match_query["rarity"] = rarity.strip()

    sort_direction = 1 if order == "asc" else -1
    if sort == "alphabet":
        sort_spec = {"_sort_name": sort_direction, "name": sort_direction, "id": 1}
    else:
        sort_spec = {"_id_is_numeric": -1, "_numeric_id": sort_direction, "id": sort_direction}

    skip = (page - 1) * limit
    projection = {"id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1}
    aggregate_projection = {"_id": 1, **projection}

    async def fetch_items() -> list[dict]:
        if sort == "alphabet":
            cursor = collection.find(match_query, projection).sort([
                ("name", sort_direction),
                ("id", 1),
            ]).skip(skip).limit(limit)
            return await cursor.to_list(length=limit)

        pipeline = [
            {"$match": match_query},
            {"$addFields": {
                "_id_is_numeric": {
                    "$regexMatch": {
                        "input": {"$toString": "$id"},
                        "regex": "^[0-9]+$"
                    }
                },
                "_numeric_id": {
                    "$convert": {
                        "input": "$id",
                        "to": "int",
                        "onError": None,
                        "onNull": None
                    }
                },
            }},
            {"$sort": sort_spec},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": aggregate_projection},
        ]
        cursor = await collection.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    total, owner_doc, items = await asyncio.gather(
        _cached_gallery_count(match_query),
        user_collection.find_one(get_user_id_query(user_id), {"characters.id": 1, "_id": 0}),
        fetch_items(),
    )

    owned_ids = set(c.get("id") for c in ((owner_doc or {}).get("characters") or []))

    for item in items:
        item["_id"] = str(item["_id"])
        item["owned"] = item.get("id") in owned_ids

    return {"total": total, "page": page, "items": items}
