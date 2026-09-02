"""DB-backed rarity configuration.

Canonical store is the `rarities` collection: one doc per rarity,
_id = rarity_id (int), with separate `emoji` and `name` fields. The display
label ("🟠 Rare") is composed as f"{emoji} {name}". load_rarities() reads
the docs into module-level dicts at startup; refresh_rarities() reloads them
IN PLACE so every importer sees edits without re-importing. The hardcoded
defaults below seed an empty collection and act as the offline fallback.
"""

import logging
import random

LOGGER = logging.getLogger(__name__)

# (rarity_id, emoji, name, spawn_weight, active_spawn_weight, shop_weight,
#  claim_weight, shop_price, stock_limit, sell_price)
# Price ladder: strictly-rarer spawn bands cost strictly more, ceiling 100⧫
# (guarded by test_default_shop_price_ladder_is_balanced).
_DEFAULT_RARITIES = [
    (1, "⚪", "Common", 360, 280, 25, 60, 1, 50, 50),
    (2, "🟢", "Medium", 240, 220, 20, 30, 2, 40, 100),
    (3, "🟠", "Rare", 110, 130, 15, 9, 4, 30, 250),
    (4, "🟡", "Legendary", 50, 70, 10, 1, 6, 20, 600),
    (5, "💠", "Cosmic", 25, 35, 8, 0, 10, 15, 1200),
    (6, "💮", "Exclusive", 4, 6, 6, 0, 30, 10, 2500),
    (7, "🔮", "Limited Edition", 2, 3, 5, 0, 45, 10, 5000),
    (8, "🫧", "Royal", 1, 2, 4, 0, 60, 5, 10000),
    (10, "🎐", "Celestial", 1, 1, 2, 0, 80, 2, 20000),
    (11, "🎞️", "Cinematic", 1, 1, 2, 0, 80, 2, 30000),
    (12, "🪽", "Prestige", 1, 1, 1, 0, 100, 1, 40000),
    (13, "❄️", "Winter", 12, 15, 6, 0, 15, 10, 1500),
    (14, "☀️", "Summer", 12, 15, 6, 0, 15, 10, 1500),
    (15, "💖", "Valentine", 5, 8, 5, 0, 25, 10, 2000),
    (16, "🎃", "Halloween", 5, 8, 5, 0, 25, 10, 2000),
    (19, "🟣", "Epic", 120, 140, 20, 0, 3, 40, 150),
    (20, "🧬", "Immortal", 25, 35, 8, 0, 10, 15, 1200),
    (21, "🌌", "Eternal", 3, 4, 6, 0, 35, 10, 2500),
    (22, "🌀", "Arcane", 2, 3, 5, 0, 45, 10, 5000),
    (23, "💎", "Mythical", 1, 2, 3, 0, 60, 5, 12000),
    (24, "✨", "Divine", 1, 1, 2, 0, 80, 2, 30000),
    (25, "🌠", "Astral", 1, 1, 1, 0, 100, 1, 40000),
    (26, "🌟", "Radiant", 8, 12, 5, 0, 20, 10, 2000),
    (27, "🌑", "Eclipse", 2, 3, 4, 0, 50, 8, 8000),
    (28, "😇", "Seraph", 1, 1, 1, 0, 90, 1, 35000),
]

NUMERIC_FIELDS = {
    "spawn_weight", "active_spawn_weight", "shop_weight", "claim_weight",
    "shop_price", "stock_limit", "sell_price",
}
TEXT_FIELDS = {"emoji", "name"}
EDITABLE_FIELDS = NUMERIC_FIELDS | TEXT_FIELDS

# Live config dicts, mutated in place by _apply_docs() so importers see refreshes.
RARITY_MAP: dict[int, str] = {}          # rarity_id -> composed label
RARITY_IDS: dict[str, int] = {}          # composed label -> rarity_id
SPAWN_RARITY_WEIGHTS: dict[str, int] = {}
ACTIVE_SPAWN_RARITY_WEIGHTS: dict[str, int] = {}
SHOP_RARITY_WEIGHTS: dict[str, int] = {}
CLAIM_RARITY_WEIGHTS: dict[str, int] = {}
RARITY_PRICES: dict[str, int] = {}
RARITY_STOCK_LIMITS: dict[str, int] = {}
SELL_PRICES: dict[str, int] = {}  # keyed by bare name ("Common")

# O(1) lookup caches for rarity_id_of(), rebuilt by _apply_docs().
_LABEL_LOOKUP: dict[str, int] = {}
_BARE_LOOKUP: dict[str, int] = {}

_RARITY_DOCS: list[dict] = []

# Max docs fetched per read; there are ~10 rarities so this is headroom.
_FETCH_LIMIT = 1000
# Sort key for docs missing an _id — pushes them to the end.
_UNSORTED_SENTINEL = 10**9


def compose_label(emoji: str, name: str) -> str:
    return f"{emoji} {name}".strip() if emoji else str(name)


def bare_name(label: str) -> str:
    """'🟢 Medium' -> 'Medium'."""
    return label.split(" ", 1)[1] if " " in label else label


def rarity_id_of(rarity: str | int | None) -> int | None:
    """Resolve a rarity_id from an id, full label, or bare name (O(1))."""
    if isinstance(rarity, int):
        return rarity if rarity in RARITY_MAP else None
    if not rarity:
        return None
    text = str(rarity).strip()
    rid = _LABEL_LOOKUP.get(text)
    if rid is not None:
        return rid
    return _BARE_LOOKUP.get(text.lower())


def label_of(rarity_id: int | None) -> str | None:
    return RARITY_MAP.get(rarity_id)


def weighted_pick(weights_map: dict[str, int]) -> str | None:
    """Pick one key from a label->weight map. None on empty/all-zero weights
    (random.choices raises on all-zero; /rarityset can zero a whole pool)."""
    if not weights_map:
        return None
    keys = list(weights_map.keys())
    weights = list(weights_map.values())
    if not any(weights):
        return None
    return random.choices(keys, weights=weights, k=1)[0]


def _default_docs() -> list[dict]:
    return [
        {
            "_id": rid, "emoji": emoji, "name": name,
            "spawn_weight": spawn, "active_spawn_weight": active,
            "shop_weight": shop, "claim_weight": claim,
            "shop_price": price, "stock_limit": stock, "sell_price": sell,
        }
        for rid, emoji, name, spawn, active, shop, claim, price, stock, sell in _DEFAULT_RARITIES
    ]


def _apply_docs(docs: list[dict]) -> None:
    global _RARITY_DOCS
    docs = sorted(docs, key=lambda d: d.get("_id", _UNSORTED_SENTINEL))
    for target in (RARITY_MAP, RARITY_IDS, SPAWN_RARITY_WEIGHTS,
                   ACTIVE_SPAWN_RARITY_WEIGHTS, SHOP_RARITY_WEIGHTS,
                   CLAIM_RARITY_WEIGHTS, RARITY_PRICES,
                   RARITY_STOCK_LIMITS, SELL_PRICES,
                   _LABEL_LOOKUP, _BARE_LOOKUP):
        target.clear()
    for doc in docs:
        rid = int(doc["_id"])
        label = compose_label(doc.get("emoji", ""), doc.get("name", ""))
        RARITY_MAP[rid] = label
        RARITY_IDS[label] = rid
        _LABEL_LOOKUP[label] = rid
        _BARE_LOOKUP[bare_name(label).lower()] = rid
        SPAWN_RARITY_WEIGHTS[label] = int(doc.get("spawn_weight", 0))
        ACTIVE_SPAWN_RARITY_WEIGHTS[label] = int(doc.get("active_spawn_weight", 0))
        SHOP_RARITY_WEIGHTS[label] = int(doc.get("shop_weight", 0))
        claim = int(doc.get("claim_weight", 0))
        if claim > 0:
            CLAIM_RARITY_WEIGHTS[label] = claim
        RARITY_PRICES[label] = int(doc.get("shop_price", 5))
        RARITY_STOCK_LIMITS[label] = int(doc.get("stock_limit", 10))
        SELL_PRICES[doc.get("name") or bare_name(label)] = int(doc.get("sell_price", 50))
    _RARITY_DOCS = docs


def get_rarity_docs() -> list[dict]:
    """Snapshot of the currently loaded rarity docs, sorted by rarity_id."""
    return [dict(d) for d in _RARITY_DOCS]


# Import-time fallback; replaced by load_rarities() once MongoDB is reachable.
_apply_docs(_default_docs())


async def _migrate_label_keyed_docs(docs: list[dict]) -> list[dict]:
    """One-time migration from the first schema (_id = full label string,
    `num` field) to the rarity_id schema (_id = int, emoji + name fields)."""
    from backend.database import rarities_collection
    migrated = []
    for doc in docs:
        label = doc["_id"]
        emoji, name = (label.split(" ", 1) + [""])[:2] if " " in label else ("", label)
        new_doc = {
            "_id": int(doc.get("num", 0)),
            "emoji": emoji,
            "name": name,
        }
        for field in NUMERIC_FIELDS:
            new_doc[field] = int(doc.get(field, 0))
        migrated.append(new_doc)
    old_ids = [doc["_id"] for doc in docs]
    await rarities_collection.delete_many({"_id": {"$in": old_ids}})
    await rarities_collection.insert_many(migrated)
    LOGGER.info("Migrated %s rarity docs to rarity_id schema.", len(migrated))
    return migrated


async def _seed_defaults_if_empty(rarities_collection) -> list:
    """Insert default docs on an empty collection, then re-fetch."""
    try:
        await rarities_collection.insert_many(_default_docs())
    except Exception as e:
        LOGGER.warning("Rarity seed insert failed (%s); re-fetching.", e)
    return await rarities_collection.find({}).to_list(length=_FETCH_LIMIT)


async def _backfill_missing_defaults(rarities_collection, docs: list) -> list:
    """Insert any default docs missing from a partially-seeded collection."""
    existing_ids = {d["_id"] for d in docs if isinstance(d["_id"], int)}
    missing = [d for d in _default_docs() if d["_id"] not in existing_ids]
    if not missing:
        return docs
    try:
        await rarities_collection.insert_many(missing)
        docs.extend(missing)
        LOGGER.info("Backfilled %s missing default rarities.", len(missing))
    except Exception as e:
        LOGGER.warning("Rarity backfill insert failed: %s", e)
    return docs


async def load_rarities() -> int:
    """Load rarities from DB, seeding from defaults on first startup."""
    from backend.database import rarities_collection
    try:
        docs = await rarities_collection.find({}).to_list(length=_FETCH_LIMIT)
        if docs and any(isinstance(d["_id"], str) for d in docs):
            docs = await _migrate_label_keyed_docs(docs)
        if not docs:
            docs = await _seed_defaults_if_empty(rarities_collection)
        else:
            # Backfill defaults missing from the collection (partial seed).
            docs = await _backfill_missing_defaults(rarities_collection, docs)
        _apply_docs(docs)
        LOGGER.info("Loaded %s rarities from database.", len(docs))
        return len(docs)
    except Exception as e:
        LOGGER.warning("Rarity load from DB failed (%s); using hardcoded defaults.", e)
        return len(_RARITY_DOCS)


async def refresh_rarities() -> int:
    """Re-read the collection into the live dicts. Returns doc count."""
    from backend.database import rarities_collection
    docs = await rarities_collection.find({}).to_list(length=_FETCH_LIMIT)
    _apply_docs(docs)
    return len(docs)


async def set_rarity_field(rarity_id: int, field: str, value) -> bool:
    """Update one field of a rarity doc and refresh the live dicts."""
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Unknown rarity field: {field}")
    from backend.database import rarities_collection
    result = await rarities_collection.update_one({"_id": rarity_id}, {"$set": {field: value}})
    if result.modified_count:
        await refresh_rarities()
    return bool(result.modified_count)


async def add_rarity(rarity_id: int, emoji: str, name: str) -> str | None:
    """Add a new rarity. Returns an error message, or None on success."""
    if rarity_id in RARITY_MAP:
        return f"Rarity id {rarity_id} already exists ({RARITY_MAP[rarity_id]})."
    label = compose_label(emoji, name)
    if label in RARITY_IDS:
        return f"Rarity {label} already exists."
    from backend.database import rarities_collection
    doc = {
        "_id": rarity_id, "emoji": emoji, "name": name,
        # Weights start at 0: out of every pool until /rarityset configures it.
        "spawn_weight": 0, "active_spawn_weight": 0,
        "shop_weight": 0, "claim_weight": 0,
        "shop_price": 5, "stock_limit": 10, "sell_price": 50,
    }
    try:
        await rarities_collection.insert_one(doc)
    except Exception as e:
        return f"Insert failed: {e}"
    await refresh_rarities()
    return None


async def rename_rarity(rarity_id: int, emoji: str, name: str) -> tuple[str, str] | None:
    """Rename/re-emoji a rarity and propagate the composed label to every
    stored copy (character docs + user harem entries). Returns
    (old_label, new_label), or None if the rarity does not exist."""
    from backend.database import collection, rarities_collection, user_collection
    old_label = RARITY_MAP.get(rarity_id)
    if old_label is None:
        return None
    new_label = compose_label(emoji, name)
    await rarities_collection.update_one(
        {"_id": rarity_id}, {"$set": {"emoji": emoji, "name": name}}
    )
    await refresh_rarities()
    if new_label != old_label:
        # Propagate the label to stored copies so read sites stay consistent.
        await collection.update_many(
            {"rarity": old_label},
            {"$set": {"rarity": new_label, "rarity_id": rarity_id}},
        )
        await user_collection.update_many(
            {"characters.rarity": old_label},
            {"$set": {"characters.$[c].rarity": new_label, "characters.$[c].rarity_id": rarity_id}},
            array_filters=[{"c.rarity": old_label}],
        )
        try:
            from backend.core.waifu import invalidate_character_cache
            invalidate_character_cache()
        except Exception:
            pass
    return old_label, new_label
