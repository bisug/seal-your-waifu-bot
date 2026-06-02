import re
import time
from copy import deepcopy
from typing import Any

from Grabber import PHOTO_URL


PET_ID_ALIASES = {
    "Fluffy Fox 🦊": "fluffy_fox",
    "Blaze Fang 🐺": "blaze_fang",
    "Shadow Panther 🐆": "shadow_panther",
    "Cosmic Phoenix 🦅": "cosmic_phoenix",
    "Mystic Dragon 🐲": "mystic_dragon",
}


def _slugify_pet_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "pet"


DEFAULT_PET = {
    "id": "fluffy_fox",
    "name": "Fluffy Fox 🦊",
    "luck": 0.10,
    "hp": 195,
    "atk": 38,
    "spd": 29,
    "level": 10,
    "xp": 0,
    "owned": True,
    "ability": "Beginner's Luck",
    "desc": "+5% XP Gain",
    "img": PHOTO_URL[0],
    "affection": 50,
    "last_interacted": 0,
}


PET_SHOP = [
    {
        "id": "blaze_fang",
        "name": "Blaze Fang 🐺",
        "luck": 0.15,
        "hp": 180,
        "atk": 30,
        "spd": 15,
        "level": 1,
        "xp": 0,
        "zenith_price": 2,
        "req_level": 0,
        "ability": "Scavenger",
        "desc": "20% Chance for Double Shards",
        "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg",
        "affection": 50,
        "last_interacted": 0,
    },
    {
        "id": "shadow_panther",
        "name": "Shadow Panther 🐆",
        "luck": 0.25,
        "hp": 140,
        "atk": 40,
        "spd": 35,
        "level": 1,
        "xp": 0,
        "zenith_price": 5,
        "req_level": 10,
        "ability": "Speedster",
        "desc": "-10s Hunt Cooldown",
        "img": "https://i.ibb.co/8CdC5QG/file-86.jpg",
        "affection": 50,
        "last_interacted": 0,
    },
    {
        "id": "cosmic_phoenix",
        "name": "Cosmic Phoenix 🦅",
        "luck": 0.35,
        "hp": 220,
        "atk": 25,
        "spd": 25,
        "level": 1,
        "xp": 0,
        "zenith_price": 12,
        "req_level": 15,
        "ability": "Caregiver",
        "desc": "50% Faster Egg Hatching",
        "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg",
        "affection": 50,
        "last_interacted": 0,
    },
    {
        "id": "mystic_dragon",
        "name": "Mystic Dragon 🐲",
        "luck": 0.50,
        "hp": 300,
        "atk": 45,
        "spd": 10,
        "level": 1,
        "xp": 0,
        "zenith_price": 25,
        "req_level": 20,
        "ability": "Hoarder",
        "desc": "5% Chance for Bonus Egg",
        "img": "https://files.catbox.moe/7kvcqj.jpg",
        "affection": 50,
        "last_interacted": 0,
    },
]


def copy_default_pet() -> dict:
    return deepcopy(DEFAULT_PET)


def pet_id_from_name(name: str | None) -> str | None:
    if not name:
        return None
    return PET_ID_ALIASES.get(name) or _slugify_pet_name(name)


def normalize_pet(pet: dict | None) -> dict:
    if not isinstance(pet, dict):
        return copy_default_pet()
    normalized = deepcopy(pet)
    name = str(normalized.get("name") or DEFAULT_PET["name"])
    normalized["name"] = name
    normalized["id"] = str(normalized.get("id") or pet_id_from_name(name))
    normalized.setdefault("luck", DEFAULT_PET["luck"])
    normalized.setdefault("hp", DEFAULT_PET["hp"])
    normalized.setdefault("atk", DEFAULT_PET["atk"])
    normalized.setdefault("spd", DEFAULT_PET["spd"])
    normalized.setdefault("level", 1)
    normalized.setdefault("xp", 0)
    normalized.setdefault("ability", "None")
    normalized.setdefault("desc", "")
    normalized.setdefault("img", DEFAULT_PET["img"])
    normalized.setdefault("affection", 50)
    normalized.setdefault("last_interacted", 0)
    return normalized


def get_pet_key(pet: dict | None) -> str | None:
    if not isinstance(pet, dict):
        return None
    return str(pet.get("id") or pet_id_from_name(pet.get("name")) or pet.get("name") or "")


def pet_matches(pet: dict | None, ref: Any) -> bool:
    if not isinstance(pet, dict) or ref is None:
        return False
    ref_str = str(ref)
    return ref_str in {str(pet.get("id") or ""), str(pet.get("name") or "")}


def find_pet(pets: list[dict], ref: Any) -> dict | None:
    return next((pet for pet in pets if pet_matches(pet, ref)), None)


def find_pet_index(pets: list[dict], ref: Any) -> int:
    return next((idx for idx, pet in enumerate(pets) if pet_matches(pet, ref)), -1)


def pet_for_storage(pet: dict) -> dict:
    stored = normalize_pet(pet)
    stored.pop("zenith_price", None)
    stored.pop("req_level", None)
    stored["owned"] = True
    return stored


def get_effective_affection(pet: dict) -> int:
    base_affection = pet.get("affection", 50)
    last_interacted = pet.get("last_interacted", 0)
    if last_interacted == 0:
        return base_affection
    days_passed = (time.time() - last_interacted) / 86400.0
    decay = int(days_passed * 5)
    return max(0, base_affection - decay)


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


async def ensure_user_pet_state(user_id: int, user: dict | None = None) -> dict:
    from Grabber.core.cache import invalidate_user_cache
    from Grabber.core.user import add_user_set_on_insert, get_user_filter
    from Grabber.database import user_collection

    if user is None:
        user = await user_collection.find_one(get_user_filter(user_id))

    original_pets = (user or {}).get("pets") if user else None
    pets = [normalize_pet(pet) for pet in (original_pets or []) if isinstance(pet, dict)]
    if not pets:
        pets = [copy_default_pet()]

    current_ref = (user or {}).get("current_pet") if user else None
    current_pet = find_pet(pets, current_ref) if current_ref else None
    if current_pet is None:
        current_pet = pets[0]
    current_key = get_pet_key(current_pet)

    needs_update = (
        user is None
        or original_pets != pets
        or (user or {}).get("current_pet") != current_key
    )
    if needs_update:
        await user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert(
                {"$set": {"pets": pets, "current_pet": current_key}},
                user_id,
            ),
            upsert=True,
        )
        await invalidate_user_cache(user_id)
        user = await user_collection.find_one(get_user_filter(user_id))

    return user or {"id": user_id, "pets": pets, "current_pet": current_key}
