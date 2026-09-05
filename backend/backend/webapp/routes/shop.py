import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.constants import (
    LEVEL_BUY_SHARD_COST,
    RARITY_PRICES,
    RARITY_STOCK_LIMITS,
    SHARDS_PER_ZENITH,
    SHOP_LIMIT,
)
from backend.core.eggs import get_egg_tier_info, normalize_egg_tier
from backend.core.leaderboard import sync_user_to_redis
from backend.core.logging import get_logger
from backend.core.pass_config import (
    CURRENT_PASS_SEASON,
    MAX_PASS_LEVEL,
    PASS_BENEFITS,
    PASS_MILESTONES,
    PASS_SEASON_NAME,
    PASS_STAR_PRICES,
    PASS_TIER_META,
    PASS_TRACKS,
    calculate_pass_upgrade_price,
    get_active_pass_type,
    get_pass_bank,
    get_pass_bank_field,
    get_pass_claims_field,
    get_pass_rank,
)
from backend.core.pass_payments import PassPaymentError, create_pass_invoice
from backend.core.progression import get_user_progress
from backend.core.roles import apply_role_discount
from backend.core.utils import get_user_id_query, normalize_user_id
from backend.database import client, collection, pokemon_catalog_collection, user_collection
from backend.modules.economy.shop import get_daily_shop_characters
from backend.webapp.auth import get_current_user, get_current_user_data
from backend.webapp.schemas import PokemonCatalogResponse

LOGGER = get_logger(__name__)

router = APIRouter()
EXCHANGE_RATE_SHARDS_PER_ZENITH = SHARDS_PER_ZENITH


def _daily_shop_timing():
    now = datetime.now(timezone.utc)
    reset_at = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "rotation_date": now.strftime("%Y-%m-%d"),
        "reset_at": reset_at.isoformat().replace("+00:00", "Z"),
    }


@router.get("/shop/hub")
async def get_shop_hub(user: dict = Depends(get_current_user_data)):
    timing = _daily_shop_timing()
    return {
        "balance": user.get("balance", 0),
        "zenith": user.get("zenith", 0),
        "pass_type": get_active_pass_type(user),
        "characters_rarity": "Various",
        "rotation_date": timing["rotation_date"],
        "reset_at": timing["reset_at"],
        "exchange_rate": EXCHANGE_RATE_SHARDS_PER_ZENITH,
    }


@router.get("/shop/exchange")
async def get_exchange_data(user: dict = Depends(get_current_user_data)):
    return {
        "balance": int(user.get("balance", 0) or 0),
        "zenith": int(user.get("zenith", 0) or 0),
        "rate": EXCHANGE_RATE_SHARDS_PER_ZENITH,
        "minimum_shards": EXCHANGE_RATE_SHARDS_PER_ZENITH,
        "minimum_zenith": 1,
    }


@router.post("/shop/exchange/{direction}")
async def exchange_currency_api(
    direction: str,
    amount: int = Query(..., ge=1),
    user_id: int = Depends(get_current_user),
):
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if direction == "shards_to_zenith":
        if amount < EXCHANGE_RATE_SHARDS_PER_ZENITH:
            raise HTTPException(status_code=400, detail=f"Minimum exchange is {EXCHANGE_RATE_SHARDS_PER_ZENITH:,} Coins")
        if amount % EXCHANGE_RATE_SHARDS_PER_ZENITH != 0:
            raise HTTPException(status_code=400, detail=f"Coins must be divisible by {EXCHANGE_RATE_SHARDS_PER_ZENITH:,}")
        zenith_amount = amount // EXCHANGE_RATE_SHARDS_PER_ZENITH
        q = get_user_id_query(user_id)
        q["balance"] = {"$gte": amount}
        update = {"$inc": {"balance": -amount, "zenith": zenith_amount, "version": 1}}
        message = f"Converted {amount:,} Coins to {zenith_amount:,} Prisms"
    elif direction == "zenith_to_shards":
        zenith_amount = amount
        shards_amount = amount * EXCHANGE_RATE_SHARDS_PER_ZENITH
        q = get_user_id_query(user_id)
        q["zenith"] = {"$gte": zenith_amount}
        update = {"$inc": {"balance": shards_amount, "zenith": -zenith_amount, "version": 1}}
        message = f"Converted {zenith_amount:,} Prisms to {shards_amount:,} Coins"
    else:
        raise HTTPException(status_code=400, detail="Invalid exchange direction")

    result = await user_collection.update_one(q, update)
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Insufficient balance for this exchange")

    await sync_user_to_redis(user_id)
    updated = await user_collection.find_one(get_user_id_query(user_id)) or {}
    return {
        "status": "success",
        "message": message,
        "balance": int(updated.get("balance", 0) or 0),
        "zenith": int(updated.get("zenith", 0) or 0),
        "rate": EXCHANGE_RATE_SHARDS_PER_ZENITH,
    }

@router.get("/shop/characters")
async def get_shop_characters(user: dict = Depends(get_current_user_data)):
    chars = await get_daily_shop_characters()
    uid_int = normalize_user_id(user["id"])
    owned_ids = set(c.get("id") for c in (user.get("characters") or []))
    
    response = []
    for c in chars:
        char_dict = c.model_dump()
        char_dict["owned"] = c.id in owned_ids
        stock_limit = RARITY_STOCK_LIMITS.get(c.rarity, SHOP_LIMIT)
        sold_count = max(0, int(char_dict.get("sold_count") or 0))
        stock_remaining = max(0, stock_limit - sold_count)
        char_dict["stock_limit"] = stock_limit
        char_dict["sold_count"] = sold_count
        char_dict["stock_remaining"] = stock_remaining
        char_dict["sold_out"] = stock_remaining <= 0
        base_price = RARITY_PRICES.get(c.rarity, 5)
        price, discount = apply_role_discount(uid_int, base_price)
        char_dict["base_zenith_price"] = base_price
        char_dict["zenith_price"] = price
        char_dict["staff_discount"] = discount
        response.append(char_dict)
    return response


@router.get("/shop/pokemon", response_model=PokemonCatalogResponse)
async def get_pokemon_catalog(
    page: int = Query(1, ge=1),
    limit: int = Query(60, ge=1, le=120),
    rarity: str | None = Query(None),
    user: dict = Depends(get_current_user_data),
):
    """Browse the Pokémon catalog (paged, optional rarity filter)."""
    query = {"enabled": True}
    if rarity:
        query["rarity"] = rarity
    cursor = pokemon_catalog_collection.find(query, {"_id": 0}).sort("sort_order", 1)
    total = await pokemon_catalog_collection.count_documents(query)
    items = await cursor.skip((page - 1) * limit).limit(limit).to_list(length=limit)
    return {"total": total, "page": page, "items": items}

@router.post("/shop/buy/character/{char_id}")
async def buy_character_api(char_id: str, user_id: int = Depends(get_current_user)):
    chars = await get_daily_shop_characters()
    shop_ids = [c.id for c in chars]
    
    if char_id not in shop_ids:
        raise HTTPException(status_code=404, detail="Character has rotated out of the shop")

    async with client.start_session() as mongo_session:
        async with await mongo_session.start_transaction():
            user_raw = await user_collection.find_one(get_user_id_query(user_id), session=mongo_session)
            if not user_raw:
                raise HTTPException(status_code=404, detail="User not found")

            char_raw = await collection.find_one({"id": char_id}, session=mongo_session)
            if not char_raw:
                raise HTTPException(status_code=404, detail="Character not found")

            base_price = RARITY_PRICES.get(char_raw.get("rarity"), 5)
            price, staff_discount = apply_role_discount(user_id, base_price)
            if user_raw.get("zenith", 0) < price:
                LOGGER.info(
                    "Shop Purchase Error: User %s has insufficient Prisms (%s) for price %s",
                    user_id,
                    user_raw.get("zenith", 0),
                    price,
                )
                raise HTTPException(status_code=400, detail=f"Insufficient Prisms (Need {price})")

            owned_ids = [c["id"] for c in user_raw.get("characters", []) if isinstance(c, dict) and "id" in c]
            if char_id in owned_ids:
                LOGGER.info("Shop Purchase Error: User %s already owns character %s", user_id, char_id)
                raise HTTPException(status_code=400, detail="You already own this character")

            stock_limit = RARITY_STOCK_LIMITS.get(char_raw.get("rarity"), SHOP_LIMIT)
            stock_update = await collection.update_one(
                {"id": char_id, "$or": [{"sold_count": {"$lt": stock_limit}}, {"sold_count": {"$exists": False}}]},
                {"$inc": {"sold_count": 1}},
                session=mongo_session,
            )
            if stock_update.modified_count == 0:
                LOGGER.info("Shop Purchase Error: Character %s is SOLD OUT (Limit: %s)", char_id, stock_limit)
                raise HTTPException(status_code=400, detail="Character is SOLD OUT")

            q = get_user_id_query(user_id)
            q["zenith"] = {"$gte": price}
            q["characters.id"] = {"$ne": char_id}
            from backend.core.rarities import rarity_id_of
            user_update = await user_collection.update_one(
                q,
                {
                    "$inc": {"zenith": -price, "char_count": 1, "version": 1},
                    "$push": {"characters": {
                        "id": char_raw["id"],
                        "name": char_raw["name"],
                        "anime": char_raw["anime"],
                        "rarity": char_raw["rarity"],
                        "rarity_id": rarity_id_of(char_raw.get("rarity")),
                        "img_url": char_raw["img_url"],
                    }},
                },
                session=mongo_session,
            )

            if user_update.modified_count == 0:
                raise HTTPException(status_code=400, detail="Purchase failed or character already owned.")

    from backend.modules.progression.achievements import check_achievements
    from backend.modules.progression.quests import update_quest_progress
    try:
        await update_quest_progress(user_id, "big_spender", price)
        await check_achievements(user_id)
    except Exception:
        LOGGER.exception("Post-purchase progression update failed for user %s", user_id)
    try:
        await sync_user_to_redis(user_id)
    except Exception:
        LOGGER.exception("Post-purchase cache sync failed for user %s", user_id)
    
    return {
        "status": "success",
        "char_name": char_raw["name"],
        "price": price,
        "base_price": base_price,
        "staff_discount": staff_discount,
    }

@router.post("/shop/pass_invoice/{tier}")
async def create_pass_invoice_api(tier: str, user_id: int = Depends(get_current_user)):
    try:
        return await create_pass_invoice(user_id, tier)
    except PassPaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/pass_data")
async def get_pass_data(user: dict = Depends(get_current_user_data)):
    uid_int = normalize_user_id(user["id"])
    
    progress = await get_user_progress(uid_int, user_data=user)
    pass_type = get_active_pass_type(user)
    pass_bank = get_pass_bank(user)
    
    return {
        "level": progress["level"],
        "xp": progress["xp"],
        "xp_current": progress["xp_current"],
        "xp_needed": progress["xp_needed"],
        "season_id": CURRENT_PASS_SEASON,
        "season_name": PASS_SEASON_NAME,
        "pass_type": pass_type,
        "pass_bank": pass_bank,
        "pass_bank_total": int(pass_bank.get("shards", 0)) + sum(
            int(v) for k, v in pass_bank.items() if str(k).startswith("eggs_t")
        ),
        "claimed_levels": progress["claimed_levels"],
        "tracks": PASS_TRACKS,
        "milestones": PASS_MILESTONES,
        "max_level": MAX_PASS_LEVEL,
        "prices": PASS_STAR_PRICES,
        "currency": "XTR",
        "upgrade_prices": {
            tier: calculate_pass_upgrade_price(pass_type, tier)
            for tier in ("premium", "elite")
        },
        "level_buy_cost": LEVEL_BUY_SHARD_COST,
        "benefits": PASS_BENEFITS,
        "tiers": PASS_TIER_META,
    }

@router.post("/claim_bank")
async def claim_pass_bank(user_id: int = Depends(get_current_user)):
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    pass_type = get_active_pass_type(user)
    if pass_type == "free":
        raise HTTPException(status_code=400, detail="Must upgrade pass to claim bank.")
        
    pass_bank = get_pass_bank(user)
    if not pass_bank or not any(int(v or 0) > 0 for v in pass_bank.values()):
        return {"message": "Bank is empty."}
        
    shards = pass_bank.get("shards", 0)
    
    eggs_to_add = []
    for k, v in pass_bank.items():
        if k.startswith("eggs_t") and v > 0:
            tier_name = normalize_egg_tier(k.split("_t")[1])
            _, tier_info = get_egg_tier_info(tier_name)
            
            for _ in range(v):
                eggs_to_add.append({
                    "id": f"bk_{uuid.uuid4().hex[:8]}",
                    "tier": tier_name,
                    "name": tier_info["name"],
                    "status": "fresh"
                })
                
    updates = {}
    if shards > 0:
        updates["$inc"] = {"balance": shards}
    if eggs_to_add:
        updates["$push"] = {"eggs": {"$each": eggs_to_add}}
        
    bank_field = get_pass_bank_field()
    updates["$unset"] = {bank_field: "", "pass_bank": ""}
    
    q = get_user_id_query(user_id)
    if isinstance((user.get("pass_bank_by_season") or {}).get(CURRENT_PASS_SEASON), dict):
        q[bank_field] = pass_bank # OCC exact bank matching
    else:
        q["pass_bank"] = pass_bank # Legacy OCC exact bank matching
    res = await user_collection.update_one(q, updates)
    
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Bank already claimed or modified.")
    
    await sync_user_to_redis(user_id)
    return {"message": f"Claimed {shards} Coins and {len(eggs_to_add)} Eggs!", "shards": shards, "eggs": len(eggs_to_add)}

@router.post("/claim_level/{level}")
async def claim_pass_level(level: int, user_id: int = Depends(get_current_user)):
    if level < 1 or level > MAX_PASS_LEVEL:
        raise HTTPException(status_code=400, detail="Invalid level")
        
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    progress = await get_user_progress(user_id, user_data=user)
    if progress["level"] < level:
        raise HTTPException(status_code=400, detail=f"Level {level} not reached yet")
        
    claimed = progress["claimed_levels"]
    if level in claimed:
        return {"status": "already_claimed", "shards": 0, "eggs": 0}
        
    reward_data = PASS_TRACKS.get(level)
    if not reward_data:
        raise HTTPException(status_code=404, detail="No rewards found for this level")
        
    pass_type = get_active_pass_type(user)
    # Rewards are cumulative (you get free + your tier)
    to_award = [reward_data["free"]]
    extra_shards = 0
    if get_pass_rank(pass_type) >= get_pass_rank("premium"):
        to_award.append(reward_data["premium"])
        extra_shards += reward_data.get("premium_extra_amount", 0)
    if pass_type == "elite":
        to_award.append(reward_data["elite"])
        extra_shards += reward_data.get("elite_extra_amount", 0)
        
    shards = 0
    eggs = []
    
    for r in to_award:
        if r["type"] == "shards":
            shards += r["amount"]
        elif r["type"] == "egg":
            tier_id = r.get("tier", 1)
            tier_name = normalize_egg_tier(tier_id)
            _, tier_info = get_egg_tier_info(tier_name)
            eggs.append({
                "id": f"bp_{level}_{uuid.uuid4().hex[:6]}",
                "tier": tier_name,
                "name": tier_info["name"],
                "status": "fresh"
            })
    shards += extra_shards
    
    # Build the $push doc up front to avoid fragile spread-merge patterns.
    push_ops: dict = {}
    if eggs:
        push_ops["eggs"] = {"$each": eggs}

    updates: dict = {
        "$addToSet": {
            get_pass_claims_field(): level,
            "claimed_levels": level,
        }
    }
    if push_ops:
        updates["$push"] = push_ops
    if shards > 0:
        updates["$inc"] = {"balance": shards}

    q = get_user_id_query(user_id)
    q[get_pass_claims_field()] = {"$ne": level} # Atomic verification: must not already contain level
    
    res = await user_collection.update_one(q, updates)
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Reward already claimed or modified.")
        
    await sync_user_to_redis(user_id)
    return {"status": "success", "shards": shards, "eggs": len(eggs)}

@router.post("/buy_level")
async def api_buy_level(levels: int = Query(1, ge=1, le=50), user_id: int = Depends(get_current_user)):
    cost = levels * LEVEL_BUY_SHARD_COST
    new_xp = None

    async with client.start_session() as mongo_session:
        async with await mongo_session.start_transaction():
            user = await user_collection.find_one(get_user_id_query(user_id), session=mongo_session)
            if not user or user.get("balance", 0) < cost:
                raise HTTPException(status_code=400, detail=f"Insufficient Coins (Need {cost})")

            deduct_result = await user_collection.update_one(
                {**get_user_id_query(user_id), "balance": {"$gte": cost}},
                {"$inc": {"balance": -cost, "version": 1}},
                session=mongo_session,
            )
            if deduct_result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Insufficient Coins (concurrent check failed)")

            from backend.core.progression import add_xp
            new_xp = await add_xp(
                user_id,
                levels * 100,
                "shop_buylevel",
                session=mongo_session,
                sync_rank=False,
            )

    if new_xp is not None:
        from backend.core.leaderboard import update_user_rank

        try:
            await update_user_rank(user_id, new_xp)
        except Exception:
            LOGGER.exception("Post-buy-level rank update failed for user %s", user_id)
    try:
        await sync_user_to_redis(user_id)
    except Exception:
        LOGGER.exception("Post-buy-level cache sync failed for user %s", user_id)
    
    return {"status": "success", "message": f"Bought {levels} levels for {cost} Coins!"}
