import logging
import re
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from config import config

LOGGER = logging.getLogger(__name__)

DEFAULT_PETID = "fluffy_fox"


PET_ID_ALIASES = {
    "Fluffy Fox 🦊": "fluffy_fox",
    "Blaze Fang 🐺": "blaze_fang",
    "Shadow Panther 🐆": "shadow_panther",
    "Cosmic Phoenix 🦅": "cosmic_phoenix",
    "Mystic Dragon 🐲": "mystic_dragon",
}


def _default_photo() -> str:
    photos = getattr(config, "PHOTO_URL", None) or []
    return photos[0] if photos else "https://files.catbox.moe/2hsawz.jpg"


PET_CATALOG_SEED = [
    {
        "petid": "fluffy_fox",
        "id": "fluffy_fox",
        "name": "Fluffy Fox 🦊",
        "rarity": "Starter",
        "hp": 105,
        "atk": 18,
        "spd": 32,
        "luck": 0.08,
        "ability": "Beginner's Luck",
        "desc": "+5% pet XP while active",
        "img": "https://files.catbox.moe/2hsawz.jpg",
        "zenith_price": 0,
        "req_level": 0,
        "sort_order": 0,
        "enabled": True,
    },
    {
        "petid": "blaze_fang",
        "id": "blaze_fang",
        "name": "Blaze Fang 🐺",
        "rarity": "Uncommon",
        "hp": 125,
        "atk": 34,
        "spd": 22,
        "luck": 0.10,
        "ability": "Scavenger",
        "desc": "20% chance for double shards",
        "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg",
        "zenith_price": 2,
        "req_level": 0,
        "sort_order": 10,
        "enabled": True,
    },
    {
        "petid": "shadow_panther",
        "id": "shadow_panther",
        "name": "Shadow Panther 🐆",
        "rarity": "Rare",
        "hp": 115,
        "atk": 28,
        "spd": 42,
        "luck": 0.14,
        "ability": "Speedster",
        "desc": "-10s hunt cooldown",
        "img": "https://i.ibb.co/8CdC5QG/file-86.jpg",
        "zenith_price": 5,
        "req_level": 10,
        "sort_order": 20,
        "enabled": True,
    },
    {
        "petid": "cosmic_phoenix",
        "id": "cosmic_phoenix",
        "name": "Cosmic Phoenix 🦅",
        "rarity": "Epic",
        "hp": 150,
        "atk": 24,
        "spd": 30,
        "luck": 0.18,
        "ability": "Caregiver",
        "desc": "50% faster egg hatching",
        "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg",
        "zenith_price": 12,
        "req_level": 15,
        "sort_order": 30,
        "enabled": True,
    },
    {
        "petid": "mystic_dragon",
        "id": "mystic_dragon",
        "name": "Mystic Dragon 🐲",
        "rarity": "Legendary",
        "hp": 180,
        "atk": 40,
        "spd": 18,
        "luck": 0.22,
        "ability": "Hoarder",
        "desc": "5% chance for a bonus egg",
        "img": "https://files.catbox.moe/7kvcqj.jpg",
        "zenith_price": 25,
        "req_level": 20,
        "sort_order": 40,
        "enabled": True,
    },
]


def _slugify_pet_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "pet"


def _clean_pet_doc(pet: dict) -> dict:
    doc = dict(pet)
    doc.pop("_id", None)
    doc.pop("created_at", None)
    doc.pop("updated_at", None)
    petid = str(doc.get("petid") or doc.get("id") or pet_id_from_name(doc.get("name")) or DEFAULT_PETID)
    doc["petid"] = petid
    doc["id"] = petid
    doc["name"] = str(doc.get("name") or petid.replace("_", " ").title())
    doc["rarity"] = str(doc.get("rarity") or "Common")
    doc["hp"] = max(1, int(doc.get("hp") or 100))
    doc["atk"] = max(1, int(doc.get("atk") or 20))
    doc["spd"] = max(1, int(doc.get("spd") or 20))
    doc["luck"] = round(max(0.0, min(0.35, float(doc.get("luck") or 0.08))), 3)
    doc["ability"] = str(doc.get("ability") or "None")
    doc["desc"] = str(doc.get("desc") or "")
    doc["img"] = str(doc.get("img") or _default_photo())
    doc["zenith_price"] = max(0, int(doc.get("zenith_price") or 0))
    doc["req_level"] = max(0, int(doc.get("req_level") or 0))
    doc["sort_order"] = int(doc.get("sort_order") or 0)
    doc["enabled"] = bool(doc.get("enabled", True))
    return doc


def clean_pet_catalog_doc(pet: dict) -> dict:
    return _clean_pet_doc(pet)


def _seed_catalog_by_id() -> dict[str, dict]:
    return {pet["petid"]: _clean_pet_doc(pet) for pet in PET_CATALOG_SEED}


def pet_id_from_name(name: str | None) -> str | None:
    if not name:
        return None
    return PET_ID_ALIASES.get(str(name)) or _slugify_pet_name(str(name))


def get_pet_key(pet: dict | None) -> str | None:
    if not isinstance(pet, dict):
        return None
    return str(
        pet.get("petid")
        or pet.get("id")
        or pet_id_from_name(pet.get("name"))
        or pet.get("name")
        or ""
    )


def get_pet_template(ref: Any) -> dict | None:
    if ref is None:
        return None
    ref_str = str(ref)
    ref_id = pet_id_from_name(ref_str)
    for pet in _seed_catalog_by_id().values():
        if ref_str in {str(pet.get("petid") or ""), str(pet.get("id") or ""), str(pet.get("name") or "")}:
            return deepcopy(pet)
        if ref_id and ref_id == str(pet.get("petid") or ""):
            return deepcopy(pet)
    return None


DEFAULT_PET = get_pet_template(DEFAULT_PETID) or _clean_pet_doc(PET_CATALOG_SEED[0])


def copy_default_pet() -> dict:
    return {
        "petid": DEFAULT_PETID,
        "level": 1,
        "xp": 0,
        "affection": 50,
        "last_interacted": 0,
    }


def normalize_pet(pet: dict | None, template: dict | None = None) -> dict:
    ownership = pet if isinstance(pet, dict) else {}
    petid = get_pet_key(ownership) or DEFAULT_PETID
    has_catalog_fields = any(key in ownership for key in ("name", "img", "hp", "atk", "spd", "luck", "ability"))
    catalog_source = template
    if catalog_source is None and has_catalog_fields:
        catalog_source = {**(get_pet_template(petid) or DEFAULT_PET), **ownership, "petid": petid, "id": petid}
    if catalog_source is None:
        catalog_source = get_pet_template(petid) or DEFAULT_PET
    catalog = _clean_pet_doc(catalog_source or DEFAULT_PET)
    normalized = deepcopy(catalog)
    normalized["petid"] = catalog["petid"]
    normalized["id"] = catalog["petid"]
    normalized["level"] = max(1, int(ownership.get("level") or 1))
    normalized["xp"] = max(0, int(ownership.get("xp") or 0))
    normalized["xp_needed"] = normalized["level"] * 100
    normalized["owned"] = bool(ownership.get("owned", True))
    normalized["affection"] = max(0, min(100, int(ownership.get("affection", 50) or 0)))
    normalized["last_interacted"] = float(ownership.get("last_interacted") or 0)
    return normalized


def pet_for_storage(pet: dict) -> dict:
    petid = get_pet_key(pet) or DEFAULT_PETID
    return {
        "petid": petid,
        "level": max(1, int(pet.get("level") or 1)),
        "xp": max(0, int(pet.get("xp") or 0)),
        "affection": max(0, min(100, int(pet.get("affection", 50) or 0))),
        "last_interacted": float(pet.get("last_interacted") or 0),
    }


def pet_matches(pet: dict | None, ref: Any) -> bool:
    if not isinstance(pet, dict) or ref is None:
        return False
    ref_str = str(ref)
    ref_id = pet_id_from_name(ref_str)
    keys = {
        str(pet.get("petid") or ""),
        str(pet.get("id") or ""),
        str(pet.get("name") or ""),
    }
    if ref_id:
        keys.add(ref_id)
    return ref_str in keys


def find_pet(pets: list[dict], ref: Any) -> dict | None:
    return next((pet for pet in pets if pet_matches(pet, ref)), None)


def find_pet_index(pets: list[dict], ref: Any) -> int:
    return next((idx for idx, pet in enumerate(pets) if pet_matches(pet, ref)), -1)


def get_effective_affection(pet: dict) -> int:
    base_affection = pet.get("affection", 50)
    last_interacted = pet.get("last_interacted", 0)
    if last_interacted == 0:
        return max(0, min(100, int(base_affection or 0)))
    days_passed = (time.time() - float(last_interacted or 0)) / 86400.0
    decay = int(days_passed * 5)
    return max(0, min(100, int(base_affection or 0) - decay))


def get_caregiver_incubation_minutes(wait_min: int, active_pet: dict | None) -> int:
    if not active_pet or active_pet.get("ability") != "Caregiver":
        return wait_min
    affection = get_effective_affection(active_pet)
    aff_multiplier = 1.0
    if affection >= 80:
        aff_multiplier = 1.2
    elif affection <= 20:
        aff_multiplier = 0.8
    return max(1, int(wait_min * (0.5 / aff_multiplier)))


async def seed_pet_catalog() -> None:
    from Grabber.database import pet_catalog_collection

    now = datetime.now(timezone.utc)
    for pet in PET_CATALOG_SEED:
        doc = _clean_pet_doc(pet)
        await pet_catalog_collection.update_one(
            {"petid": doc["petid"]},
            {
                "$setOnInsert": {**doc, "created_at": now},
            },
            upsert=True,
        )


async def upsert_catalog_pet(pet: dict) -> dict:
    from Grabber.database import pet_catalog_collection

    now = datetime.now(timezone.utc)
    doc = _clean_pet_doc(pet)
    await pet_catalog_collection.update_one(
        {"petid": doc["petid"]},
        {
            "$set": {**doc, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    return doc


async def list_pet_catalog(include_disabled: bool = False, shop_only: bool = False) -> list[dict]:
    from Grabber.database import pet_catalog_collection

    query: dict[str, Any] = {}
    if not include_disabled:
        query["enabled"] = {"$ne": False}
    if shop_only:
        query["zenith_price"] = {"$gt": 0}

    try:
        cursor = pet_catalog_collection.find(query).sort("sort_order", 1)
        pets = [_clean_pet_doc(pet) async for pet in cursor]
        if pets:
            return pets

        await seed_pet_catalog()
        cursor = pet_catalog_collection.find(query).sort("sort_order", 1)
        pets = [_clean_pet_doc(pet) async for pet in cursor]
        if pets:
            return pets
    except Exception as exc:
        LOGGER.warning("Pet catalog DB lookup failed; using seed catalog fallback: %s", exc)

    pets = [_clean_pet_doc(pet) for pet in PET_CATALOG_SEED]
    if not include_disabled:
        pets = [pet for pet in pets if pet.get("enabled") is not False]
    if shop_only:
        pets = [pet for pet in pets if int(pet.get("zenith_price") or 0) > 0]
    return sorted(pets, key=lambda pet: int(pet.get("sort_order") or 0))


async def list_shop_pets() -> list[dict]:
    return await list_pet_catalog(shop_only=True)


async def get_catalog_pet(ref: Any, include_disabled: bool = False) -> dict | None:
    if ref is None:
        return None
    ref_str = str(ref)
    ref_id = pet_id_from_name(ref_str)
    for pet in await list_pet_catalog(include_disabled=include_disabled):
        if ref_str in {str(pet.get("petid") or ""), str(pet.get("id") or ""), str(pet.get("name") or "")}:
            return deepcopy(pet)
        if ref_id and ref_id == str(pet.get("petid") or ""):
            return deepcopy(pet)
    return None


async def get_shop_pet(ref: Any) -> dict | None:
    shop_pets = await list_shop_pets()
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        index = int(ref)
        if 0 <= index < len(shop_pets):
            return deepcopy(shop_pets[index])
    ref_str = str(ref)
    ref_id = pet_id_from_name(ref_str)
    for pet in shop_pets:
        if ref_str in {str(pet.get("petid") or ""), str(pet.get("id") or ""), str(pet.get("name") or "")}:
            return deepcopy(pet)
        if ref_id and ref_id == str(pet.get("petid") or ""):
            return deepcopy(pet)
    return None


async def _normalize_user_pets(raw_pets: list) -> tuple[list[dict], list[dict]]:
    catalog = {pet["petid"]: pet for pet in await list_pet_catalog()}
    stored: list[dict] = []
    enriched: list[dict] = []
    seen: set[str] = set()

    for raw_pet in raw_pets:
        if not isinstance(raw_pet, dict):
            continue
        petid = get_pet_key(raw_pet) or DEFAULT_PETID
        template = catalog.get(petid) or get_pet_template(petid) or DEFAULT_PET
        pet = normalize_pet(raw_pet, template)
        petid = pet["petid"]
        if petid in seen:
            continue
        seen.add(petid)
        stored.append(pet_for_storage(pet))
        enriched.append(pet)

    if not stored:
        default_template = catalog.get(DEFAULT_PETID) or DEFAULT_PET
        default_pet = normalize_pet(copy_default_pet(), default_template)
        stored = [pet_for_storage(default_pet)]
        enriched = [default_pet]

    return stored, enriched


async def ensure_user_pet_state(user_id: int, user: dict | None = None) -> dict:
    from Grabber.core.cache import invalidate_user_cache
    from Grabber.core.user import add_user_set_on_insert, get_user_filter
    from Grabber.database import user_collection

    if user is None:
        user = await user_collection.find_one(get_user_filter(user_id))

    original_pets = (user or {}).get("pets") if user else None
    stored_pets, enriched_pets = await _normalize_user_pets(original_pets or [])

    current_ref = (user or {}).get("current_pet") if user else None
    current_pet = find_pet(enriched_pets, current_ref) if current_ref else None
    if current_pet is None:
        current_pet = enriched_pets[0]
    current_key = get_pet_key(current_pet)

    needs_update = (
        user is None
        or original_pets != stored_pets
        or (user or {}).get("current_pet") != current_key
    )
    if needs_update:
        await user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert(
                {"$set": {"pets": stored_pets, "current_pet": current_key}},
                user_id,
            ),
            upsert=True,
        )
        await invalidate_user_cache(user_id)
        user = await user_collection.find_one(get_user_filter(user_id))

    enriched_user = dict(user or {"id": user_id})
    enriched_user["pets"] = enriched_pets
    enriched_user["current_pet"] = current_key
    return enriched_user
