"""Pokémon engine: catalog access, user ownership, active Pokémon resolution.

Users own Pokémon via `user.pokemon` (list of {dex, level, xp}) and select one
via `user.current_pokemon` (dex int). Catalog lives in `pokemon_catalog`.
"""

import random

from backend.core.logging import get_logger
from backend.core.utils import get_now_utc
from backend.database import pokemon_catalog_collection, user_collection

LOGGER = get_logger(__name__)

STARTER_DEXES = (1, 4, 7, 25, 133)  # Bulbasaur, Charmander, Squirtle, Pikachu, Eevee
XP_PER_LEVEL = 100
# Level at which a Pokémon evolves to its next chain stage. Later stages
# cost more: stage 1→2 at 16, 2→3 at 32 (mirrors the games' mid/late evolutions).
EVOLVE_LEVELS = (16, 32)


def normalize_pokemon(entry: dict, catalog: dict | None = None) -> dict:
    """Merge a user-owned entry with its catalog doc into a display payload."""
    cat = catalog or {}
    level = int(entry.get("level", 1))
    return {
        "dex": int(entry.get("dex", cat.get("dex", 0))),
        "name": cat.get("name", f"Pokemon #{entry.get('dex', '?')}"),
        "types": cat.get("types", []),
        "img": cat.get("img", ""),
        "shiny_img": cat.get("shiny_img"),
        "cry": cat.get("cry"),
        "base_stats": cat.get("base_stats", {}),
        "base_total": cat.get("base_total", 0),
        "height_dm": cat.get("height_dm"),
        "weight_hg": cat.get("weight_hg"),
        "abilities": cat.get("abilities", []),
        "moves": cat.get("moves", []),
        "desc": cat.get("desc"),
        "flavor_text": cat.get("flavor_text"),
        "growth_rate": cat.get("growth_rate"),
        "gender_rate": cat.get("gender_rate"),
        "capture_rate": cat.get("capture_rate"),
        "base_happiness": cat.get("base_happiness"),
        "egg_groups": cat.get("egg_groups", []),
        "evolves_from": cat.get("evolves_from"),
        "evolution_chain": cat.get("evolution_chain", []),
        "is_legendary": cat.get("is_legendary", False),
        "is_mythical": cat.get("is_mythical", False),
        "generation": cat.get("generation"),
        "level": level,
        "xp": int(entry.get("xp", 0)),
        "xp_needed": level * XP_PER_LEVEL,
        "is_active": False,  # caller sets on the active one
    }


async def get_catalog_pokemon(dex: int) -> dict | None:
    return await pokemon_catalog_collection.find_one({"dex": int(dex)})


async def list_catalog_pokemon(enabled_only: bool = True, limit: int = 0) -> list[dict]:
    query = {"enabled": True} if enabled_only else {}
    cursor = pokemon_catalog_collection.find(query, {"_id": 0}).sort("sort_order", 1)
    if limit:
        cursor = cursor.limit(limit)
    return await cursor.to_list(length=None)


async def ensure_user_pokemon_state(user_id: int, user: dict | None = None) -> dict:
    """Guarantee `pokemon` list + `current_pokemon` exist on the user doc."""
    user = user or await user_collection.find_one({"id": int(user_id)}) or {}
    if "pokemon" in user and "current_pokemon" in user:
        return user
    # $setOnInsert is a no-op for existing users; $set only the missing fields.
    patch = {}
    if "pokemon" not in user:
        patch["pokemon"] = []
    if "current_pokemon" not in user:
        patch["current_pokemon"] = None
    if patch:
        await user_collection.update_one({"id": int(user_id)}, {"$set": patch})
    user.setdefault("pokemon", [])
    user.setdefault("current_pokemon", None)
    return user


def find_pokemon(owned: list[dict], ref) -> dict | None:
    """Find an owned entry by dex (int/str) — None if not owned."""
    try:
        dex = int(ref)
    except (TypeError, ValueError):
        return None
    return next((p for p in owned if int(p.get("dex", -1)) == dex), None)


async def get_active_pokemon(user_id: int, user: dict | None = None) -> dict | None:
    """(owned entry + catalog) for the user's current Pokémon, or None."""
    user = await ensure_user_pokemon_state(user_id, user)
    current = user.get("current_pokemon")
    if current is None:
        return None
    entry = find_pokemon(user.get("pokemon", []), current)
    if not entry:
        return None
    catalog = await get_catalog_pokemon(entry["dex"])
    return normalize_pokemon(entry, catalog)


async def set_active_pokemon(user_id: int, dex: int) -> bool:
    user = await ensure_user_pokemon_state(user_id)
    if not find_pokemon(user.get("pokemon", []), dex):
        return False
    await user_collection.update_one(
        {"id": int(user_id)},
        {"$set": {"current_pokemon": int(dex)}},
    )
    return True


async def grant_pokemon(user_id: int, dex: int, level: int = 1) -> bool:
    """Add a Pokémon to the user's collection. Returns False if already owned."""
    dex = int(dex)
    catalog = await get_catalog_pokemon(dex)
    if not catalog:
        return False
    res = await user_collection.update_one(
        {"id": int(user_id), "pokemon.dex": {"$ne": dex}},
        {"$push": {"pokemon": {"dex": dex, "level": int(level), "xp": 0, "obtained_at": get_now_utc()}}},
    )
    return res.modified_count > 0


async def add_pokemon_xp(
    user_id: int, xp: int, source: str = "activity"
) -> tuple[int | None, dict | None]:
    """Add XP to the active Pokémon; level up at level*XP_PER_LEVEL.

    Returns (new_level, evolution) where evolution is None or
    {"from": dex, "to": dex, "from_name": str, "to_name": str}.
    """
    active = await get_active_pokemon(user_id)
    if not active:
        return None, None
    dex = active["dex"]
    user = await user_collection.find_one(
        {"id": int(user_id), "pokemon.dex": dex},
        {"pokemon.$": 1},
    )
    if not user:
        return None, None
    entry = user["pokemon"][0]
    level = int(entry.get("level", 1))
    xp_now = int(entry.get("xp", 0)) + int(xp)
    while xp_now >= level * XP_PER_LEVEL:
        xp_now -= level * XP_PER_LEVEL
        level += 1
    await user_collection.update_one(
        {"id": int(user_id), "pokemon.dex": dex},
        {"$set": {"pokemon.$.level": level, "pokemon.$.xp": xp_now}},
    )
    LOGGER.debug("pokemon xp: user=%s dex=%s +%s -> lvl %s (%s)", user_id, dex, xp, level, source)
    evolution = await evolve_pokemon(user_id, dex)
    return level, evolution


def _evolve_threshold(chain: list[int], dex: int) -> int:
    """Level required to evolve from this stage (later stages cost more)."""
    idx = chain.index(dex) if dex in chain else 0
    return EVOLVE_LEVELS[min(idx, len(EVOLVE_LEVELS) - 1)]


async def evolve_pokemon(user_id: int, dex: int) -> dict | None:
    """Evolve an owned Pokémon to its next chain stage if the level threshold is met.

    Successors come from the catalog's `evolves_from` field (exact even for
    branch points like Eevee). Branching lines pick a random next stage.
    Skips if every target is already owned (no duplicate dexes).
    Returns {"from", "to", "from_name", "to_name"} or None.
    """
    dex = int(dex)
    catalog = await get_catalog_pokemon(dex)
    if not catalog:
        return None
    successors = await pokemon_catalog_collection.find(
        {"evolves_from": dex, "enabled": True}, {"_id": 0, "dex": 1, "name": 1}
    ).to_list(length=None)
    if not successors:
        return None
    user = await user_collection.find_one(
        {"id": int(user_id), "pokemon.dex": dex}, {"pokemon": 1, "current_pokemon": 1}
    )
    if not user:
        return None
    entry = find_pokemon(user.get("pokemon", []), dex)
    if not entry or int(entry.get("level", 1)) < _evolve_threshold(
        catalog.get("evolution_chain") or [], dex
    ):
        return None
    owned_dexes = {int(p.get("dex", -1)) for p in user.get("pokemon", [])}
    candidates = [s for s in successors if s["dex"] not in owned_dexes]
    if not candidates:
        return None
    target = random.choice(candidates)
    res = await user_collection.update_one(
        {"id": int(user_id), "pokemon.dex": dex},
        {"$set": {"pokemon.$.dex": target["dex"]}},
    )
    if res.modified_count == 0:
        return None
    if user.get("current_pokemon") == dex:
        await user_collection.update_one(
            {"id": int(user_id)}, {"$set": {"current_pokemon": target["dex"]}}
        )
    LOGGER.info("pokemon evolve: user=%s %s -> %s", user_id, dex, target["dex"])
    return {
        "from": dex,
        "to": target["dex"],
        "from_name": catalog["name"],
        "to_name": target["name"],
    }


def battle_stats(pokemon: dict) -> dict:
    """Combat stats for battle.py, scaled by level (mirrors old pet scaling)."""
    level = int(pokemon.get("level", 1))
    base = pokemon.get("base_stats") or {}
    hp = int(base.get("hp", 50)) + level * 5
    atk = int((int(base.get("atk", 50)) + int(base.get("spatk", 50))) / 2) + level * 2
    spd = int(base.get("spd", 50)) + level * 1
    return {
        "name": pokemon["name"],
        "types": pokemon.get("types", []),
        "hp": hp,
        "atk": atk,
        "spd": spd,
        "luck": 0.05,
        "level": level,
        "max_hp": hp,
    }
