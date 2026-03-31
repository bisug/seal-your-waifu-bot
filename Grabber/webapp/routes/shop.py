from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio
from typing import Dict
from collections import defaultdict
import uuid
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.database import user_collection, collection
from Grabber.core.constants import SHOP_RARITY, SHOP_LIMIT, DEFAULT_ZENITH_PRICE, PASS_PRICES
from Grabber.modules.economy.shop import get_daily_shop_characters
from Grabber.modules.progression.pet import PET_SHOP
from Grabber.core.pass_data import PASS_TRACKS, MAX_PASS_LEVEL
from Grabber.core.progression import get_user_progress

from Grabber.webapp.auth import get_current_user, get_current_user_data, _user_locks

router = APIRouter()

def get_user_id_query(user_id):
    try:
        uid_int = int(user_id)
        return {"id": {"$in": [uid_int, str(uid_int)]}}
    except (ValueError, TypeError):
        return {"id": str(user_id)}

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

from Grabber.core.constants import SHOP_RARITY, SHOP_LIMIT, RARITY_PRICES, PASS_PRICES
from Grabber.modules.economy.shop import get_daily_shop_characters

async def buy_character_api(char_id: str, user_id: int = Depends(get_current_user)):
    uid_str = str(user_id)
    
    # Critical section: Lock exact user so spam clicks don't bypass checks
    async with _user_locks[uid_str]:
        user_raw = await user_collection.find_one(get_user_id_query(user_id))
        if not user_raw: raise HTTPException(status_code=404, detail="User not found")
        
        char_raw = await collection.find_one({"id": char_id})
        if not char_raw or char_raw.get("rarity") != SHOP_RARITY:
            raise HTTPException(status_code=404, detail="Character not available in shop")
        
        price = RARITY_PRICES.get(char_raw.get("rarity"), 5)
        if user_raw.get("zenith", 0) < price:
            from Grabber import LOGGER
            LOGGER.info(f"Shop Purchase Error: User {user_id} has insufficient Zenith ({user_raw.get('zenith', 0)}) for price {price}")
            raise HTTPException(status_code=400, detail=f"Insufficient Zenith (Need {price})")
            
        owned_ids = [c["id"] for c in user_raw.get("characters", []) if isinstance(c, dict) and "id" in c]
        if char_id in owned_ids:
            from Grabber import LOGGER
            LOGGER.info(f"Shop Purchase Error: User {user_id} already owns character {char_id}")
            raise HTTPException(status_code=400, detail="You already own this character")

        stock_update = await collection.update_one(
            {"id": char_id, "sold_count": {"$lt": SHOP_LIMIT}},
            {"$inc": {"sold_count": 1}}
        )
        if stock_update.modified_count == 0:
            from Grabber import LOGGER
            LOGGER.info(f"Shop Purchase Error: Character {char_id} is SOLD OUT (Limit: {SHOP_LIMIT})")
            raise HTTPException(status_code=400, detail="Character is SOLD OUT")

        q = get_user_id_query(user_id)
        q["zenith"] = {"$gte": price}
        user_update = await user_collection.update_one(
            q,
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

        from Grabber.modules.progression.quests import update_quest_progress
        from Grabber.modules.progression.achievements import check_achievements
        await update_quest_progress(user_id, "big_spender", price)
        await check_achievements(user_id)
        
        return {"status": "success", "char_name": char_raw["name"]}

@router.get("/shop/pets")
async def get_shop_pets(user: dict = Depends(get_current_user_data)):
    owned_pet_names = [p["name"] for p in user.get("pets", [])]
    uid_int = user["id"]
    if isinstance(uid_int, list): uid_int = uid_int[0]
    
    return {
        "pets": PET_SHOP,
        "owned": owned_pet_names,
        "current_level": (await get_user_progress(uid_int))["level"]
    }

@router.post("/shop/buy/pet/{pet_index}")
async def buy_pet_api(pet_index: int, user_id: int = Depends(get_current_user)):
    uid_str = str(user_id)
    async with _user_locks[uid_str]:
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
    
    uid_str = str(user_id)
    async with _user_locks[uid_str]:
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
        await user_collection.update_one(
            q,
            {"$set": {"pass_type": tier}, "$inc": {"zenith": -price}}
        )
        return {"status": "success", "new_tier": tier}

@router.get("/pass_data")
async def get_pass_data(user: dict = Depends(get_current_user_data)):
    uid_int = user["id"]
    if isinstance(uid_int, list): uid_int = uid_int[0]
    
    progress = await get_user_progress(uid_int, user_data=user)
    
    return {
        "level": progress["level"],
        "pass_type": user.get("pass_type", "free"),
        "pass_bank": user.get("pass_bank", {"shards": 0}),
        "claimed_levels": user.get("pass_claimed", []),
        "tracks": PASS_TRACKS,
        "max_level": MAX_PASS_LEVEL
    }

@router.post("/claim_bank")
async def claim_pass_bank(user_id: int = Depends(get_current_user)):
    uid_str = str(user_id)
    async with _user_locks[uid_str]:
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
        
        await user_collection.update_one(get_user_id_query(user_id), updates)
        
        return {"message": f"Claimed {shards} Shards and {len(eggs_to_add)} Eggs!", "shards": shards, "eggs": len(eggs_to_add)}

@router.post("/buy_level")
async def api_buy_level(levels: int = Query(1, ge=1, le=50), user_id: int = Depends(get_current_user)):
    uid_str = str(user_id)
    async with _user_locks[uid_str]:
        cost = levels * 5000
        user = await user_collection.find_one(get_user_id_query(user_id))
        
        if not user or user.get("balance", 0) < cost:
            raise HTTPException(status_code=400, detail=f"Insufficient Shards (Need {cost})")
            
        await user_collection.update_one(get_user_id_query(user_id), {"$inc": {"balance": -cost}})
        
        from Grabber.core.progression import add_xp
        await add_xp(user_id, levels * 100, "shop_buylevel")
        
        return {"status": "success", "message": f"Bought {levels} levels for {cost} Shards!"}
