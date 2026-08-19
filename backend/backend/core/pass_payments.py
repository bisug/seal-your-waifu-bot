import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from config import config
from backend import LOGGER
from backend.core.cache import sync_user_to_redis
from backend.core.pass_config import (
    CURRENT_PASS_SEASON,
    PASS_SEASON_NAME,
    PASS_TIERS,
    calculate_pass_upgrade_price,
    get_active_pass_type,
    get_pass_rank,
    normalize_pass_tier,
)
from backend.core.user import get_user_filter
from backend.database import star_orders_collection, user_collection

PAYMENT_CURRENCY = "XTR"
PASS_ORDER_TTL = timedelta(minutes=45)
PASS_PAYMENT_LOCK_TTL = timedelta(minutes=10)


class PassPaymentError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime | None) -> datetime | None:
    if not dt:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _build_payload(season_id: str, tier: str, order_id: str) -> str:
    return f"pass:{season_id}:{tier}:{order_id}"


def _payment_lock_field() -> str:
    return f"pass_payment_locks.{CURRENT_PASS_SEASON}"


def parse_pass_payload(payload: str | bytes | None) -> dict[str, str] | None:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode()
        except UnicodeDecodeError:
            return None
    if not isinstance(payload, str):
        return None
    parts = payload.split(":")
    if len(parts) != 4 or parts[0] != "pass":
        return None
    return {
        "season_id": parts[1],
        "tier": normalize_pass_tier(parts[2]),
        "order_id": parts[3],
    }


def _telegram_api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{config.TOKEN}/{method}"


async def create_pass_invoice(user_id: int, tier: str) -> dict[str, Any]:
    tier = normalize_pass_tier(tier)
    if tier == "free":
        raise PassPaymentError("Free pass does not require payment.")

    user = await user_collection.find_one(get_user_filter(user_id))
    if not user:
        raise PassPaymentError("Open the bot once before buying the pass.")

    current_tier = get_active_pass_type(user)
    amount = calculate_pass_upgrade_price(current_tier, tier)
    if amount is None:
        raise PassPaymentError("You already have this pass tier or better.")

    order_id = f"po_{uuid.uuid4().hex[:18]}"
    payload = _build_payload(CURRENT_PASS_SEASON, tier, order_id)
    now = _now()
    await star_orders_collection.update_many(
        {
            "user_id": int(user_id),
            "kind": "pass_upgrade",
            "season_id": CURRENT_PASS_SEASON,
            "status": "pending",
        },
        {"$set": {"status": "superseded", "superseded_at": now}},
    )

    order = {
        "order_id": order_id,
        "payload": payload,
        "kind": "pass_upgrade",
        "user_id": int(user_id),
        "season_id": CURRENT_PASS_SEASON,
        "season_name": PASS_SEASON_NAME,
        "tier": tier,
        "current_tier": current_tier,
        "amount": amount,
        "currency": PAYMENT_CURRENCY,
        "status": "pending",
        "created_at": now,
        "expires_at_dt": now + PASS_ORDER_TTL,
    }
    await star_orders_collection.insert_one(order)

    body = {
        "title": f"{tier.capitalize()} Seal Pass",
        "description": f"{PASS_SEASON_NAME} {tier.capitalize()} Battle Pass",
        "payload": payload,
        "currency": PAYMENT_CURRENCY,
        "prices": [{"label": f"{tier.capitalize()} Pass", "amount": amount}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(_telegram_api_url("createInvoiceLink"), json=body)
            data = response.json()
    except Exception as exc:
        await star_orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "invoice_failed", "error": str(exc), "failed_at": _now()}},
        )
        raise PassPaymentError("Could not create Telegram Stars invoice.") from exc

    if not data.get("ok") or not data.get("result"):
        await star_orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "invoice_failed", "error": data, "failed_at": _now()}},
        )
        description = data.get("description") if isinstance(data, dict) else None
        raise PassPaymentError(description or "Could not create Telegram Stars invoice.")

    invoice_url = data["result"]
    await star_orders_collection.update_one(
        {"order_id": order_id},
        {"$set": {"invoice_url": invoice_url, "invoice_created_at": _now()}},
    )

    return {
        "order_id": order_id,
        "invoice_url": invoice_url,
        "tier": tier,
        "amount": amount,
        "currency": PAYMENT_CURRENCY,
        "expires_at": order["expires_at_dt"].isoformat(),
    }


async def validate_pass_precheckout(pre_checkout_query) -> tuple[bool, str | None]:
    parsed = parse_pass_payload(getattr(pre_checkout_query, "invoice_payload", None))
    if not parsed:
        return False, "Unknown pass order."

    order = await star_orders_collection.find_one({"order_id": parsed["order_id"]})
    if not order:
        return False, "This pass order expired. Please create a new invoice."
    if order.get("status") not in {"pending", "precheckout"}:
        return False, "This pass order is no longer payable."
    if order.get("season_id") != CURRENT_PASS_SEASON:
        return False, "This pass season is no longer active."
    if order.get("currency") != getattr(pre_checkout_query, "currency", None):
        return False, "Currency mismatch."
    if int(order.get("amount", 0)) != int(getattr(pre_checkout_query, "total_amount", 0)):
        return False, "Amount mismatch."
    if int(order.get("user_id", 0)) != int(pre_checkout_query.from_user.id):
        return False, "This invoice belongs to another user."
    expires_at = _as_aware(order.get("expires_at_dt"))
    if expires_at and expires_at < _now():
        return False, "This pass order expired. Please create a new invoice."

    user = await user_collection.find_one(get_user_filter(pre_checkout_query.from_user.id))
    current_tier = get_active_pass_type(user)
    if get_pass_rank(current_tier) >= get_pass_rank(order["tier"]):
        return False, "You already have this pass tier or better."
    expected_amount = calculate_pass_upgrade_price(current_tier, order["tier"])
    if expected_amount is None or int(expected_amount) != int(order.get("amount", 0)):
        return False, "This pass price changed. Please create a new invoice."

    lock_field = _payment_lock_field()
    lock_filter = get_user_filter(pre_checkout_query.from_user.id)
    lock_filter["$or"] = [
        {lock_field: {"$exists": False}},
        {f"{lock_field}.order_id": order["order_id"]},
        {f"{lock_field}.expires_at": {"$lt": _now()}},
    ]
    lock_result = await user_collection.update_one(
        lock_filter,
        {
            "$set": {
                lock_field: {
                    "order_id": order["order_id"],
                    "tier": order["tier"],
                    "amount": order["amount"],
                    "currency": order["currency"],
                    "expires_at": _now() + PASS_PAYMENT_LOCK_TTL,
                }
            }
        },
    )
    if lock_result.modified_count == 0:
        return False, "Another pass payment is already being processed."

    reserve_result = await star_orders_collection.update_one(
        {"order_id": order["order_id"], "status": {"$in": ["pending", "precheckout"]}},
        {
            "$set": {
                "status": "precheckout",
                "precheckout_at": _now(),
                "precheckout_query_id": getattr(pre_checkout_query, "id", None),
            }
        },
    )
    if reserve_result.modified_count == 0:
        await user_collection.update_one(get_user_filter(pre_checkout_query.from_user.id), {"$unset": {lock_field: ""}})
        return False, "This pass order is no longer payable."

    return True, None


async def fulfill_pass_payment(user_id: int, successful_payment) -> dict[str, Any]:
    parsed = parse_pass_payload(getattr(successful_payment, "invoice_payload", None))
    if not parsed:
        return {"status": "ignored", "reason": "unknown_payload"}

    amount = int(getattr(successful_payment, "total_amount", 0))
    currency = getattr(successful_payment, "currency", None)
    charge_id = getattr(successful_payment, "telegram_payment_charge_id", None)
    provider_charge_id = getattr(successful_payment, "provider_payment_charge_id", None)

    order = await star_orders_collection.find_one({"order_id": parsed["order_id"]})
    if not order:
        LOGGER.warning("Stars payment received for missing pass order payload=%s", successful_payment.invoice_payload)
        return {"status": "ignored", "reason": "missing_order"}

    if order.get("status") == "fulfilled":
        return {"status": "already_fulfilled", "tier": order.get("tier")}

    if int(order.get("user_id", 0)) != int(user_id):
        LOGGER.warning("Stars payment user mismatch for order %s", order.get("order_id"))
        return {"status": "ignored", "reason": "user_mismatch"}
    if order.get("currency") != currency or int(order.get("amount", 0)) != amount:
        LOGGER.warning("Stars payment amount/currency mismatch for order %s", order.get("order_id"))
        return {"status": "ignored", "reason": "amount_mismatch"}

    payment_fields = {
        "status": "fulfilling",
        "paid_at": _now(),
    }
    if charge_id:
        payment_fields["telegram_payment_charge_id"] = charge_id
    if provider_charge_id:
        payment_fields["provider_payment_charge_id"] = provider_charge_id

    claim = await star_orders_collection.update_one(
        {"order_id": order["order_id"], "status": {"$in": ["pending", "precheckout", "paid"]}},
        {"$set": payment_fields},
    )
    if claim.modified_count == 0:
        return {"status": "already_processing", "tier": order.get("tier")}

    tier = normalize_pass_tier(order["tier"])
    user = await user_collection.find_one(get_user_filter(user_id)) or {}
    current_tier = get_active_pass_type(user)
    activated = get_pass_rank(current_tier) < get_pass_rank(tier)
    now = _now()
    lock_field = _payment_lock_field()

    if activated:
        target_rank = get_pass_rank(tier)
        lower_tiers = [candidate for candidate in PASS_TIERS if get_pass_rank(candidate) < target_rank]
        activation_filter = get_user_filter(user_id)
        activation_filter["$or"] = [
            {f"pass_entitlements.{CURRENT_PASS_SEASON}.tier": {"$in": lower_tiers}},
            {f"pass_entitlements.{CURRENT_PASS_SEASON}.tier": {"$exists": False}, "pass_type": {"$in": lower_tiers}},
            {f"pass_entitlements.{CURRENT_PASS_SEASON}.tier": {"$exists": False}, "pass_type": {"$exists": False}},
        ]
        activation_result = await user_collection.update_one(
            activation_filter,
            {
                "$set": {
                    "pass_type": tier,
                    "season": CURRENT_PASS_SEASON,
                    f"pass_entitlements.{CURRENT_PASS_SEASON}": {
                        "tier": tier,
                        "source": "telegram_stars",
                        "order_id": order["order_id"],
                        "amount": amount,
                        "currency": currency,
                        "rank": target_rank,
                        "activated_at": now,
                    },
                },
                "$push": {
                    "pass_purchases": {
                        "order_id": order["order_id"],
                        "tier": tier,
                        "season_id": CURRENT_PASS_SEASON,
                        "amount": amount,
                        "currency": currency,
                        "telegram_payment_charge_id": charge_id,
                        "created_at": now,
                    }
                },
                "$unset": {lock_field: ""},
            },
        )
        activated = activation_result.modified_count > 0
        if activated:
            await sync_user_to_redis(user_id)

    await user_collection.update_one(get_user_filter(user_id), {"$unset": {lock_field: ""}})

    await star_orders_collection.update_one(
        {"order_id": order["order_id"]},
        {
            "$set": {
                "status": "fulfilled",
                "fulfilled_at": _now(),
                "activated": activated,
                "final_tier": tier,
            }
        },
    )

    return {"status": "fulfilled", "tier": tier, "activated": activated}
