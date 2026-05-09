from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from Grabber.database import user_collection, sessions_collection
from Grabber.webapp.auth import get_current_user, get_current_user_data
from Grabber.core.utils import get_user_id_query, normalize_user_id
from Grabber.webapp.schemas import TradeOffer, MarriageModel, ReferralModel, BattleStatsModel, CharacterModel
from Grabber.core.cache import sync_user_to_redis
import uuid

router = APIRouter()

# --- TRADING ---

@router.get("/trade/offers", response_model=List[TradeOffer])
async def get_trade_offers(user_id: int = Depends(get_current_user)):
    # Simple implementation: fetch pending trades from a temporary collection or user doc
    # For now, let's assume they are stored in a session-like collection
    cursor = sessions_collection.find({"type": "trade_offer", "$or": [{"sender_id": user_id}, {"receiver_id": user_id}]})
    offers = await cursor.to_list(length=100)
    return [TradeOffer(**o) for o in offers]

@router.post("/trade/offer")
async def create_trade_offer(
    receiver_id: int = Body(...),
    sender_char_id: str = Body(...),
    receiver_char_id: str = Body(...),
    user: dict = Depends(get_current_user_data)
):
    sender_id = normalize_user_id(user["id"])
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")

    receiver = await user_collection.find_one(get_user_id_query(receiver_id))
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    sender_char = next((c for c in user.get("characters", []) if c["id"] == sender_char_id), None)
    receiver_char = next((c for c in receiver.get("characters", []) if c["id"] == receiver_char_id), None)

    if not sender_char or not receiver_char:
        raise HTTPException(status_code=400, detail="Character not found in harem")

    trade_id = str(uuid.uuid4())
    offer = {
        "id": trade_id,
        "type": "trade_offer",
        "sender_id": sender_id,
        "sender_name": user.get("first_name", "Unknown"),
        "receiver_id": receiver_id,
        "receiver_name": receiver.get("first_name", "Unknown"),
        "sender_char": sender_char,
        "receiver_char": receiver_char,
        "status": "pending"
    }
    await sessions_collection.insert_one(offer)
    return {"status": "success", "trade_id": trade_id}

@router.post("/trade/respond/{trade_id}")
async def respond_to_trade(
    trade_id: str,
    action: str = Body(..., pattern="^(accept|reject)$"),
    user_id: int = Depends(get_current_user)
):
    offer = await sessions_collection.find_one({"id": trade_id, "type": "trade_offer"})
    if not offer:
        raise HTTPException(status_code=404, detail="Trade offer not found")

    if offer["receiver_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if action == "reject":
        await sessions_collection.delete_one({"id": trade_id})
        return {"status": "rejected"}

    # Accept Logic
    sender_id = offer["sender_id"]
    s_char = offer["sender_char"]
    r_char = offer["receiver_char"]

    # Atomically swap characters
    # This is a simplified version of the logic in Grabber/modules/social/trade.py
    try:
        # Sender gives s_char, receives r_char
        res1 = await user_collection.update_one(
            {"id": {"$in": [sender_id, str(sender_id)]}, "characters.id": s_char["id"]},
            {"$set": {"characters.$": r_char}}
        )
        if res1.modified_count == 0:
            raise ValueError("Sender character no longer available")

        # Receiver gives r_char, receives s_char
        res2 = await user_collection.update_one(
            {"id": {"$in": [user_id, str(user_id)]}, "characters.id": r_char["id"]},
            {"$set": {"characters.$": s_char}}
        )
        if res2.modified_count == 0:
            # Rollback res1
            await user_collection.update_one(
                {"id": {"$in": [sender_id, str(sender_id)]}, "characters.id": r_char["id"]},
                {"$set": {"characters.$": s_char}}
            )
            raise ValueError("Receiver character no longer available")

        await sessions_collection.delete_one({"id": trade_id})
        await sync_user_to_redis(sender_id)
        await sync_user_to_redis(user_id)
        return {"status": "accepted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- MARRIAGE ---

@router.get("/social/marriage", response_model=Optional[MarriageModel])
async def get_marriage(user: dict = Depends(get_current_user_data)):
    partner_id = user.get("married_to")
    if not partner_id:
        return None

    partner = await user_collection.find_one(get_user_id_query(partner_id))
    return {
        "partner_id": partner_id,
        "partner_name": partner.get("first_name", "Unknown") if partner else "Unknown",
        "partner_avatar": partner.get("avatar") if partner else None,
        "married_at": user.get("married_at", "Unknown")
    }

# --- REFERRALS ---

@router.get("/social/referrals", response_model=List[ReferralModel])
async def get_referrals(user: dict = Depends(get_current_user_data)):
    referrals = user.get("referrals", [])
    # Enrich referral data
    enriched = []
    for ref_id in referrals:
        ref_user = await user_collection.find_one(get_user_id_query(ref_id))
        enriched.append({
            "referred_id": ref_id,
            "referred_name": ref_user.get("first_name", "Unknown") if ref_user else "Unknown",
            "rewarded": True # Simplified
        })
    return enriched

# --- BATTLE STATS ---

@router.get("/battle/stats", response_model=BattleStatsModel)
async def get_battle_stats(user: dict = Depends(get_current_user_data)):
    total = user.get("total_battles", 0)
    wins = user.get("wins", 0)
    losses = total - wins
    win_rate = (wins / total * 100) if total > 0 else 0
    return {
        "total_battles": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }
