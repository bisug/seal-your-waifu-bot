import uuid
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pymongo import ReturnDocument

from backend.core.leaderboard import sync_user_to_redis
from backend.core.logging import get_logger
from backend.core.referrals import get_referral_stats as build_referral_stats
from backend.core.referrals import normalize_referral_ids
from backend.core.utils import get_now_utc, get_user_id_query, normalize_user_id
from backend.database import client, sessions_collection, user_collection
from backend.webapp.auth import get_current_user, get_current_user_data
from backend.webapp.schemas import (
    BattleStatsModel,
    MarriageModel,
    ReferralModel,
    ReferralStatsModel,
    TradeOffer,
)

LOGGER = get_logger(__name__)
router = APIRouter()
TRADE_OFFER_TTL = timedelta(hours=24)

# --- TRADING ---

@router.get("/trade/offers", response_model=List[TradeOffer])
async def get_trade_offers(user_id: int = Depends(get_current_user)):
    now = get_now_utc()
    query = {
        "type": "trade_offer",
        "$and": [
            {
                "$or": [
                    {"sender_id": user_id},
                    {"receiver_id": user_id},
                ]
            },
            {
                "$or": [
                    {"expires_at_dt": {"$exists": False}},
                    {"expires_at_dt": {"$gt": now}},
                ]
            },
        ]
    }
    cursor = sessions_collection.find(query)
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
    now = get_now_utc()
    offer = {
        "id": trade_id,
        "type": "trade_offer",
        "sender_id": sender_id,
        "sender_name": user.get("first_name", "Unknown"),
        "receiver_id": receiver_id,
        "receiver_name": receiver.get("first_name", "Unknown"),
        "sender_char": sender_char,
        "receiver_char": receiver_char,
        "status": "pending",
        "created_at_dt": now,
        "expires_at_dt": now + TRADE_OFFER_TTL,
    }
    await sessions_collection.insert_one(offer)
    return {"status": "success", "trade_id": trade_id}

@router.post("/trade/respond/{trade_id}")
async def respond_to_trade(
    trade_id: str,
    action: str = Body(..., embed=True, pattern="^(accept|reject)$"),
    user_id: int = Depends(get_current_user)
):
    now = get_now_utc()
    active_offer_filter = {
        "id": trade_id,
        "type": "trade_offer",
        "$or": [
            {"expires_at_dt": {"$exists": False}},
            {"expires_at_dt": {"$gt": now}},
        ],
    }
    offer = await sessions_collection.find_one(active_offer_filter)
    if not offer:
        raise HTTPException(status_code=404, detail="Trade offer not found")

    if normalize_user_id(offer["receiver_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if action == "reject":
        deleted = await sessions_collection.delete_one({**active_offer_filter, "status": "pending"})
        if deleted.deleted_count == 0:
            raise HTTPException(status_code=409, detail="Trade offer is already being handled")
        return {"status": "rejected"}

    locked_offer = await sessions_collection.find_one_and_update(
        {**active_offer_filter, "status": "pending"},
        {"$set": {"status": "processing"}},
        return_document=ReturnDocument.AFTER
    )
    if not locked_offer:
        raise HTTPException(status_code=409, detail="Trade offer is already being handled")

    sender_id = locked_offer["sender_id"]
    s_char = locked_offer["sender_char"]
    r_char = locked_offer["receiver_char"]

    try:
        async with client.start_session() as mongo_session:
            async with await mongo_session.start_transaction():
                res1 = await user_collection.update_one(
                    {**get_user_id_query(sender_id), "characters.id": s_char["id"]},
                    {"$set": {"characters.$": r_char}, "$inc": {"version": 1}},
                    session=mongo_session
                )
                if res1.modified_count == 0:
                    raise ValueError("Sender character no longer available")

                res2 = await user_collection.update_one(
                    {**get_user_id_query(user_id), "characters.id": r_char["id"]},
                    {"$set": {"characters.$": s_char}, "$inc": {"version": 1}},
                    session=mongo_session
                )
                if res2.modified_count == 0:
                    raise ValueError("Receiver character no longer available")

        await sessions_collection.delete_one({"id": trade_id})
        await sync_user_to_redis(sender_id)
        await sync_user_to_redis(user_id)
        return {"status": "accepted"}
    except ValueError as e:
        # Expected business failure (character moved mid-trade): offer is dead.
        await sessions_collection.update_one(
            {"id": trade_id, "type": "trade_offer"},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Unexpected (DB hiccup, txn abort): release the processing lock so the
        # user can retry instead of bricking the offer, and never leak internals.
        LOGGER.exception("Trade acceptance failed for offer %s", trade_id)
        await sessions_collection.update_one(
            {"id": trade_id, "type": "trade_offer", "status": "processing"},
            {"$set": {"status": "pending"}}
        )
        raise HTTPException(status_code=500, detail="Trade could not be completed. Please try again.") from e

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
    referrals = normalize_referral_ids(user.get("referrals", []))
    if not referrals:
        return []

    ref_query_ids = [normalize_user_id(rid) for rid in referrals]

    cursor = user_collection.find({"id": {"$in": ref_query_ids}})
    ref_users = await cursor.to_list(length=100)

    ref_map = {}
    for u in ref_users:
        first_name = u.get("first_name", "Unknown")
        uid = normalize_user_id(u.get("id"))
        ref_map[uid] = first_name
        ref_map[str(uid)] = first_name

    event_map = {}
    for event in user.get("referral_events", []):
        if not isinstance(event, dict):
            continue
        uid = normalize_user_id(event.get("user_id"))
        first_name = event.get("first_name")
        if uid and first_name:
            event_map[uid] = first_name

    return [
        {
            "referred_id": rid,
            "referred_name": ref_map.get(rid) or ref_map.get(str(rid)) or event_map.get(rid) or "Unknown",
            "rewarded": True
        } for rid in referrals
    ]

@router.get("/social/referrals/stats", response_model=ReferralStatsModel)
async def get_referrals_stats(user: dict = Depends(get_current_user_data)):
    return build_referral_stats(user)

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
