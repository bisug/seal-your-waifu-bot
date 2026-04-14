from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio
import uuid
from Grabber import LOGGER
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.database import user_collection, collection
from Grabber.core.cache import sync_user_to_redis
from Grabber.core.constants import SHOP_RARITY, SHOP_LIMIT, RARITY_PRICES, PASS_PRICES
from Grabber.modules.economy.shop import get_daily_shop_characters
from Grabber.modules.progression.pet import PET_SHOP
from Grabber.core.pass_config import PASS_TRACKS, MAX_PASS_LEVEL
from Grabber.core.progression import get_user_progress
from Grabber.core.utils import normalize_user_id

router = APIRouter()

from Grabber.core.utils import get_user_id_query

@router.get("/shop/hub")
async def get_shop_hub(user: dict = Depends(get_current_user_data)):
    return {
        "balance": user.get("balance", 0),
        "zenith": user.get("zenith", 0),
        "pass_type": user.get("pass_type", "free"),
        "characters_rarity": SHOP_RARITY
    }

@router.get("/shop/characters")
async def get_shop_characters(user: dict = Depends(get_current_user_data)):
    chars = await get_daily_shop_characters()
    owned_ids = set(c.get("id") for c in (user.get("characters") or []))
    
    response = []
    for c in chars:
        char_dict = c.dict()
        char_dict["owned"] = c.id in owned_ids
        char_dict["stock_limit"] = SHOP_LIMIT
        char_dict["zenith_price"] = RARITY_PRICES.get(c.rarity, 5)
        response.append(char_dict)
    return response

@router.post("/shop/buy/character/{char_id}")
async def buy_character_api(char_id: str, user_id: int = Depends(get_current_user)):
    user_raw = await user_collection.find_one(get_user_id_query(user_id))
    if not user_raw: raise HTTPException(status_code=404, detail="User not found")
    
    chars = await get_daily_shop_characters()
    shop_ids = [c.id for c in chars]
    
    if char_id not in shop_ids:
        raise HTTPException(status_code=404, detail="Character has rotated out of the shop")
        
    char_raw = await collection.find_one({"id": char_id})
    if not char_raw:
        raise HTTPException(status_code=404, detail="Character not found")

        price = RARITY_PRICES.get(char_raw.get("rarity"), 5)
        if user_raw.get("zenith", 0) < price:
            LOGGER.info(f"Shop Purchase Error: User {user_id} has insufficient Zenith ({user_raw.get('zenith', 0)}) for price {price}")
            raise HTTPException(status_code=400, detail=f"Insufficient Zenith (Need {price})")
            
        owned_ids = [c["id"] for c in user_raw.get("characters", []) if isinstance(c, dict) and "id" in c]
        if char_id in owned_ids:
            LOGGER.info(f"Shop Purchase Error: User {user_id} already owns character {char_id}")
            raise HTTPException(status_code=400, detail="You already own this character")

    stock_update = await collection.update_one(
        {"id": char_id, "sold_count": {"$lt": SHOP_LIMIT}},
        {"$inc": {"sold_count": 1}}
    )
    if stock_update.modified_count == 0:
        LOGGER.info(f"Shop Purchase Error: Character {char_id} is SOLD OUT (Limit: {SHOP_LIMIT})")
        raise HTTPException(status_code=400, detail="Character is SOLD OUT")

    q = get_user_id_query(user_id)
    q["zenith"] = {"$gte": price}
    q["characters.id"] = {"$ne": char_id} # Atomic OCC guard against duplicate purchase
    user_update = await user_collection.update_one(
        q,
        {
            "$inc": {"zenith": -price, "char_count": 1},
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
        raise HTTPException(status_code=400, detail="Transaction failed or character already owned.")

    from Grabber.modules.progression.quests import update_quest_progress
    from Grabber.modules.progression.achievements import check_achievements
    await update_quest_progress(user_id, "big_spender", price)
    await check_achievements(user_id)
    await sync_user_to_redis(user_id)
    
    return {"status": "success", "char_name": char_raw["name"]}

@router.get("/shop/pets")
async def get_shop_pets(user: dict = Depends(get_current_user_data)):
    owned_pet_names = [p["name"] for p in user.get("pets", [])]
    uid_int = normalize_user_id(user["id"])
    
    return {
        "pets": PET_SHOP,
        "owned": owned_pet_names,
        "current_level": (await get_user_progress(uid_int))["level"]
    }

@router.post("/shop/buy/pet/{pet_index}")
async def buy_pet_api(pet_index: int, user_id: int = Depends(get_current_user)):
    from Grabber.modules.progression.pet import perform_pet_purchase
    result = await perform_pet_purchase(user_id, pet_index, user_collection, get_user_id_query)
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
    
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    current_tier = user.get("pass_type", "free")
    tiers_order = ["free", "premium", "elite"]
    if tiers_order.index(current_tier) >= tiers_order.index(tier):
        raise HTTPException(status_code=400, detail="You already have this tier or higher")
        
    price = PASS_PRICES[tier]
    if user.get("zenith", 0) < price:
        raise HTTPException(status_code=400, detail=f"Insufficient Zenith (Need {price})")
        
    q = get_user_id_query(user_id)
    q["zenith"] = {"$gte": price}
    q["pass_type"] = current_tier # OCC strict matching
    update_result = await user_collection.update_one(
        q,
        {"$set": {"pass_type": tier}, "$inc": {"zenith": -price}}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Transaction failed or tier already upgraded.")
        
    await sync_user_to_redis(user_id)
    return {"status": "success", "new_tier": tier}

@router.get("/pass_data")
async def get_pass_data(user: dict = Depends(get_current_user_data)):
    uid_int = normalize_user_id(user["id"])
    
    progress = await get_user_progress(uid_int, user_data=user)
    
    return {
        "level": progress["level"],
        "pass_type": user.get("pass_type", "free"),
        "pass_bank": user.get("pass_bank", {"shards": 0}),
        "claimed_levels": user.get("claimed_levels", []),
        "tracks": PASS_TRACKS,
        "max_level": MAX_PASS_LEVEL
    }

@router.post("/claim_bank")
async def claim_pass_bank(user_id: int = Depends(get_current_user)):
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    pass_type = user.get("pass_type", "free")
    if pass_type == "free":
        raise HTTPException(status_code=400, detail="Must upgrade pass to claim bank.")
        
    pass_bank = user.get("pass_bank", {})
    if not pass_bank:
        return {"message": "Bank is empty."}
        
    shards = pass_bank.get("shards", 0)
    
    eggs_to_add = []
    for k, v in pass_bank.items():
        if k.startswith("eggs_t") and v > 0:
            tier = k.split("_t")[1]
            if tier == "1": tier_name = "gold"
            elif tier == "2": tier_name = "void"
            else: tier_name = "common"
            
            for _ in range(v):
                eggs_to_add.append({
                    "id": f"bk_{uuid.uuid4().hex[:8]}",
                    "tier": tier_name,
                    "name": f"{tier_name.capitalize()} Egg",
                    "status": "fresh"
                })
                
    updates = {}
    if shards > 0:
        updates["$inc"] = {"balance": shards}
    if eggs_to_add:
        updates["$push"] = {"eggs": {"$each": eggs_to_add}}
        
    updates["$unset"] = {"pass_bank": ""}
    
    q = get_user_id_query(user_id)
    q["pass_bank"] = pass_bank # OCC exact bank matching
    res = await user_collection.update_one(q, updates)
    
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Bank already claimed or modified.")
    
    return {"message": f"Claimed {shards} Shards and {len(eggs_to_add)} Eggs!", "shards": shards, "eggs": len(eggs_to_add)}

@router.post("/claim_level/{level}")
async def claim_pass_level(level: int, user_id: int = Depends(get_current_user)):
    if level < 1 or level > MAX_PASS_LEVEL:
        raise HTTPException(status_code=400, detail="Invalid level")
        
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    progress = await get_user_progress(user_id, user_data=user)
    if progress["level"] < level:
        raise HTTPException(status_code=400, detail=f"Level {level} not reached yet")
        
    claimed = user.get("claimed_levels", [])
    if level in claimed:
        raise HTTPException(status_code=400, detail="Level reward already claimed")
        
    reward_data = PASS_TRACKS.get(level)
    if not reward_data:
        raise HTTPException(status_code=404, detail="No rewards found for this level")
        
    pass_type = user.get("pass_type", "free")
    # Rewards are cumulative (you get free + your tier)
    to_award = [reward_data["free"]]
    if pass_type != "free":
        to_award.append(reward_data[pass_type])
        
    shards = 0
    eggs = []
    
    for r in to_award:
        if r["type"] == "shards":
            shards += r["amount"]
        elif r["type"] == "egg":
            tier_id = r.get("tier", 1)
            tier_names = {1: "gold", 2: "void", 3: "rare", 4: "legendary", 5: "celestial"}
            tier_name = tier_names.get(tier_id, "gold")
            eggs.append({
                "id": f"bp_{level}_{uuid.uuid4().hex[:6]}",
                "tier": tier_name,
                "name": f"{tier_name.capitalize()} Egg",
                "status": "fresh"
            })
    
    # Build the $push doc up front to avoid fragile spread-merge patterns.
    push_ops: dict = {"claimed_levels": level}
    if eggs:
        push_ops["eggs"] = {"$each": eggs}

    updates: dict = {"$push": push_ops}
    if shards > 0:
        updates["$inc"] = {"balance": shards}

    q = get_user_id_query(user_id)
    q["claimed_levels"] = {"$ne": level} # Atomic verification: must not already contain level
    
    res = await user_collection.update_one(q, updates)
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Reward already claimed or modified.")
        
    return {"status": "success", "shards": shards, "eggs": len(eggs)}

@router.post("/buy_level")
async def api_buy_level(levels: int = Query(1, ge=1, le=50), user_id: int = Depends(get_current_user)):
    cost = levels * 5000
    user = await user_collection.find_one(get_user_id_query(user_id))
    
    if not user or user.get("balance", 0) < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient Shards (Need {cost})")
        
    deduct_result = await user_collection.update_one(
        {**get_user_id_query(user_id), "balance": {"$gte": cost}},
        {"$inc": {"balance": -cost}}
    )
    if deduct_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Insufficient Shards (concurrent check failed)")
    
    try:
        from Grabber.core.progression import add_xp
        await add_xp(user_id, levels * 100, "shop_buylevel")
    except Exception as e:
        LOGGER.error(f"buy_level XP add failed for user {user_id}, rolling back: {e}")
        await user_collection.update_one(get_user_id_query(user_id), {"$inc": {"balance": cost}})
        raise HTTPException(status_code=500, detail="Transaction failed. Your shards have been refunded.")
    
    return {"status": "success", "message": f"Bought {levels} levels for {cost} Shards!"}
