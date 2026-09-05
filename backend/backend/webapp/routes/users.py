import asyncio
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from backend.core.eggs import (
    get_egg_purify_price,
    get_egg_sell_price,
    get_egg_tier_info,
    get_incubating_count,
    get_incubation_wait_minutes,
)
from backend.core.minigames import get_user_energy
from backend.core.pass_config import (
    apply_pass_incubation_bonus,
    get_active_pass_type,
    get_pass_incubation_slots,
)
from backend.core.pokemon import normalize_pokemon
from backend.core.progression import get_level_from_xp, get_user_progress
from backend.core.roles import get_role_payload
from backend.core.tasks import run_background_task
from backend.core.cache import invalidate_user_cache
from backend.core.user import get_user_rank_with_fallback
from backend.core.utils import get_user_id_query, normalize_user_id
from backend.database import collection, pokemon_catalog_collection, user_collection
from backend.modules.progression.achievements import ACHIEVEMENTS
from backend.webapp.auth import get_current_user, get_current_user_data, is_sudo_user_id
from backend.webapp.schemas import UserProfileResponse
from config import config

router = APIRouter()

# The character catalog size changes rarely (only on uploads), so cache the
# estimated count instead of hitting Mongo on every /me request.
_TOTAL_AVAILABLE_TTL = 300
_total_available_cache: dict[str, object] = {"expires_at": 0.0, "count": 0}


async def _cached_total_available_characters() -> int:
    import time as _time
    now = _time.monotonic()
    if now < float(_total_available_cache["expires_at"]) and _total_available_cache["count"]:
        return int(_total_available_cache["count"])
    count = await collection.estimated_document_count()
    _total_available_cache["count"] = count
    _total_available_cache["expires_at"] = now + _TOTAL_AVAILABLE_TTL
    return count


@router.get("/bot/info")
async def get_bot_info():
    """Public endpoint to get bot identity for branding."""
    return {
        "name": getattr(config, "BOT_NAME", "SEAL YOUR WAIFU"),
        "username": getattr(config, "BOT_USERNAME", "SealYourWaifuBot"),
        "id": getattr(config, "BOT_ID", None),
        "avatar": config.PHOTO_URL[0] if config.PHOTO_URL else "https://files.catbox.moe/2hsawz.jpg"
    }

@router.get("/achievements/list")
async def get_achievements_list(user_id: int = Depends(get_current_user)):
    """Return all possible achievements and whether the user has them."""
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_achievements = set(user.get("achievements") or [])

    all_achievements = []
    for ach_id, data in ACHIEVEMENTS.items():
        all_achievements.append({
            "id": ach_id,
            "name": data["name"],
            "description": data["description"],
            "icon": data.get("symbol", "✦"),
            "reward_xp": data.get("reward_xp", 0),
            "unlocked": ach_id in user_achievements
        })

    return all_achievements

def _enrich_achievements(raw_ids: list) -> list:
    """Map raw achievement ids to their catalog entries (id, name, icon)."""
    return [
        {
            "id": ach_id,
            "name": ACHIEVEMENTS[ach_id]["name"],
            "icon": ACHIEVEMENTS[ach_id].get("symbol", "✦"),
        }
        for ach_id in raw_ids
        if ach_id in ACHIEVEMENTS
    ]


def _clean_titles(user: dict) -> tuple[str, list[str]]:
    """Strip non-ASCII from titles; default to Rookie when absent."""
    titles_list = user.get("titles") or ["Rookie"]
    clean = [re.sub(r'[^\x00-\x7F]+', '', str(t or "").strip()) for t in titles_list]
    source = user.get("title") or (titles_list[-1] if titles_list else "Rookie")
    current = re.sub(r'[^\x00-\x7F]+', '', str(source or "Rookie")).strip()
    return current, clean


def _collection_stats(user: dict, total_available: int) -> tuple[int, int, float]:
    """(total copies, unique characters, completion percent) from the user doc."""
    characters = user.get("characters") or []
    total = user.get("char_count")
    if total is None:
        total = len(characters)
    unique = len({
        str(char.get("id"))
        for char in characters
        if isinstance(char, dict) and char.get("id") is not None
    })
    percent = (
        round((unique / total_available) * 100, 1)
        if total_available > 0 else 0.0
    )
    return total, unique, percent


def _process_eggs(user: dict, pass_type) -> tuple[list, bool]:
    """Normalize egg docs for the response; flag legacy string eggs for migration."""
    eggs = user.get("eggs", [])
    processed = []
    migration_needed = False
    for egg in eggs:
        if isinstance(egg, str):
            migration_needed = True
            tier_key, tier_info = get_egg_tier_info(egg)
            base_wait_min = get_incubation_wait_minutes(tier_key)
            wait_min = apply_pass_incubation_bonus(base_wait_min, user)
            processed.append({
                "id": f"mig_{str(uuid.uuid4())[:12]}",
                "tier": tier_key,
                "name": tier_info["name"],
                "status": "fresh",
                "is_corrupted": False,
                "hatch_time": None,
                "remaining_mins": 0,
                "base_wait_min": base_wait_min,
                "wait_min": wait_min,
            })
            continue

        tier_key, tier_info = get_egg_tier_info(egg.get("tier", "common"))
        base_wait_min = get_incubation_wait_minutes(tier_key)
        wait_min = apply_pass_incubation_bonus(base_wait_min, user)
        h_time = egg.get("hatch_time")
        rem_mins = 0
        if h_time and isinstance(h_time, datetime):
            if h_time.tzinfo is None:
                h_time = h_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if now < h_time:
                rem_mins = int((h_time - now).total_seconds() / 60)
            h_time = h_time.isoformat()

        processed.append({
            "id": egg.get("id"),
            "tier": tier_key,
            "name": egg.get("name") or tier_info["name"],
            "status": egg.get("status", "fresh"),
            "is_corrupted": egg.get("is_corrupted", False),
            "hatch_time": h_time,
            "remaining_mins": rem_mins,
            "base_wait_min": int(egg.get("incubation_base_minutes") or base_wait_min),
            "wait_min": int(egg.get("incubation_minutes") or wait_min),
            "incubation_pass_type": egg.get("incubation_pass_type") or pass_type,
            "sell_price": get_egg_sell_price(tier_key),
            "purify_price": get_egg_purify_price(tier_key),
        })
    return processed, migration_needed


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: dict = Depends(get_current_user_data)):
    user_id = normalize_user_id(user["id"])

    user_xp = user.get("xp", 0)

    # Rank, progress, catalog count and energy are independent of each other —
    # run them concurrently instead of chaining sequential awaits.
    rank_result, progress, total_available_characters, energy_result = await asyncio.gather(
        get_user_rank_with_fallback(user_id, user_xp),
        get_user_progress(user_id, user_data=user),
        _cached_total_available_characters(),
        get_user_energy(user_id, user_data=user),
    )
    rank, total_users, percentile = rank_result
    energy, last_recharge = energy_result

    
    enriched_achievements = _enrich_achievements(user.get("achievements") or [])
    current_title, clean_titles = _clean_titles(user)
    
    total_characters, unique_characters, collection_percent = _collection_stats(
        user, total_available_characters
    )
    
    eggs = user.get("eggs", [])
    pass_type = get_active_pass_type(user)
    incubation_slots = get_pass_incubation_slots(user)
    active_incubations = get_incubating_count(eggs)
    role_payload = get_role_payload(user_id)

    resp_data = {
        "id": int(user_id),
        "first_name": (user.get("first_name") or "User"),
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "avatar": user.get("avatar"),
        "is_sudo": is_sudo_user_id(user_id),
        "terms_accepted": bool(user.get("terms_accepted_at")),
        **role_payload,
        "balance": user.get("balance", 0),
        "zenith": user.get("zenith", 0),
        "stats": {
            "level": progress["level"],
            "xp": progress["xp"],
            "xp_needed": max(progress["xp_needed"], 1),
            "xp_current": min(progress["xp_current"], progress["xp_needed"]),
            "streak": user.get("streak", 0),
            "points": user.get("balance", 0),
            "zenith": user.get("zenith", 0),
            "badges": user.get("badges") or [],
            "total_characters": total_characters,
            "unique_characters": unique_characters,
            "total_available_characters": total_available_characters,
            "collection_percent": collection_percent,
            "rank": rank,
            "percentile": percentile,
            "pass_type": pass_type,
            "incubation_slots": incubation_slots,
            "active_incubations": active_incubations,
            "energy": energy,
            "last_energy_recharge": last_recharge.isoformat() if last_recharge else None
        },
        "achievements": enriched_achievements,
        "titles": {
            "current": current_title,
            "all": clean_titles
        },
        "eggs": []
    }

    processed_eggs, migration_needed = _process_eggs(user, pass_type)
    resp_data["eggs"] = processed_eggs
    
    # Pokémon block: owned list + active, normalized against the catalog.
    owned_pokemon = user.get("pokemon") or []
    owned_dexes = [p.get("dex") for p in owned_pokemon]
    catalog_docs = (
        await pokemon_catalog_collection.find(
            {"dex": {"$in": owned_dexes}}, {"_id": 0}
        ).to_list(length=None)
        if owned_dexes else []
    )
    catalog_map = {c["dex"]: c for c in catalog_docs}
    resp_data["pokemon"] = [
        normalize_pokemon(p, catalog_map.get(p.get("dex"))) for p in owned_pokemon
    ]
    active_ref = user.get("current_pokemon")
    active_entry = next((p for p in owned_pokemon if p.get("dex") == active_ref), None)
    resp_data["current_pokemon"] = (
        normalize_pokemon(active_entry, catalog_map.get(active_ref)) if active_entry is not None else None
    )
    
    if migration_needed:
        derived_fields = {"remaining_mins", "wait_min", "base_wait_min"}
        db_eggs = [{k: v for k, v in e.items() if k not in derived_fields} for e in processed_eggs]
        run_background_task(user_collection.update_one(
            get_user_id_query(int(user_id)),
            {"$set": {"eggs": db_eggs}}
        ))
    
    return resp_data


@router.get("/profile", include_in_schema=False)
async def get_profile_legacy():
    """Backward compatibility for old client versions."""
    return RedirectResponse(url="./me", status_code=307)


@router.post("/terms/accept")
async def accept_terms(user_id: int = Depends(get_current_user)):
    """Record the user's terms acceptance. Idempotent — re-accepting is a no-op."""
    now = datetime.now(timezone.utc)
    result = await user_collection.update_one(
        get_user_id_query(user_id),
        {"$set": {"terms_accepted_at": now, "terms_version": 1}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    # /me reads through the Redis user cache; without this the gate would
    # stay visible for up to TTL_USER (60s) after accepting.
    await invalidate_user_cache(user_id)
    return {"status": "success", "accepted_at": now.isoformat()}


@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("harem", pattern="^(harem|shards|zenith|level|guesses)$"),
    limit: int = Query(50, ge=1, le=100)
):
    from backend.modules.info.leaderboard import METRICS, get_top_users
    users = await get_top_users(metric, limit)
    
    field = METRICS[metric]["field"]
    response_data = []
    for i, u in enumerate(users, 1):
        user_id = u.get("id")
        first_name = (u.get("first_name") or "").strip()
        username = u.get("username")
        if not first_name or first_name.lower() == "user":
            first_name = username or f"Collector {str(user_id)[-4:] if user_id else i}"
        last_name = u.get("last_name")
        full_name = f"{first_name} {last_name}" if last_name else first_name

        processed = {
            "rank": i,
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "username": username,
            "value": u.get(field, 0),
            "avatar": u.get("avatar") 
        }
        if metric == "level":
            processed["level"] = get_level_from_xp(processed["value"])
        response_data.append(processed)
        
    return response_data
