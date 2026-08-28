"""DB-backed rarity configuration.

Canonical store is the `rarities` collection (one doc per rarity,
_id = full label such as "🟠 Rare"). load_rarities() reads the docs into
module-level dicts at startup; refresh_rarities() reloads them IN PLACE so
every module that imported a dict sees edits without re-importing.

The hardcoded defaults below seed an empty collection on first startup and
act as the fallback when MongoDB is unreachable.
"""

import logging

LOGGER = logging.getLogger(__name__)

# (num, label, spawn_weight, active_spawn_weight, shop_weight, claim_weight,
#  shop_price, stock_limit, sell_price)
_DEFAULT_RARITIES = [
    (1, "⚪ Common", 360, 280, 25, 60, 1, 50, 50),
    (2, "🟢 Medium", 240, 220, 20, 30, 2, 40, 100),
    (3, "🟠 Rare", 110, 130, 15, 9, 5, 30, 250),
    (4, "🟡 Legendary", 50, 70, 10, 1, 10, 20, 600),
    (5, "💠 Cosmic", 25, 35, 8, 0, 25, 15, 1200),
    (6, "💮 Exclusive", 4, 6, 6, 0, 50, 10, 2500),
    (7, "🔮 Limited Edition", 2, 3, 5, 0, 100, 10, 5000),
    (8, "🫧 Royal", 1, 2, 4, 0, 250, 5, 10000),
    (9, "💎 Antique", 1, 2, 3, 0, 500, 5, 12000),
    (10, "🎐 Celestial", 1, 1, 2, 0, 1000, 2, 20000),
    (11, "🎞️ AMV", 1, 1, 2, 0, 1500, 2, 30000),
    (12, "🪽 Prestige", 1, 1, 1, 0, 2500, 1, 40000),
    (13, "❄️ Winter", 12, 15, 6, 0, 50, 10, 1500),
    (14, "☀️ Summer", 12, 15, 6, 0, 50, 10, 1500),
    (15, "💖 Valentine", 5, 8, 5, 0, 100, 10, 2000),
    (16, "🎃 Halloween", 5, 8, 5, 0, 100, 10, 2000),
    (17, "💸 Luxury", 8, 12, 4, 0, 250, 5, 2500),
    (18, "🎏 Limited", 18, 25, 10, 0, 200, 20, 1800),
    (19, "🟣 Epic", 120, 140, 20, 0, 2, 40, 150),
    (20, "🧬 Immortal", 25, 35, 8, 0, 25, 15, 1200),
    (21, "🌌 Eternal", 3, 4, 6, 0, 50, 10, 2500),
    (22, "🔮 Mystic", 2, 3, 5, 0, 100, 10, 5000),
    (23, "💎 Mythical", 1, 2, 3, 0, 500, 5, 12000),
    (24, "✨ Divine", 1, 1, 2, 0, 1500, 2, 30000),
    (25, "🌠 Astral", 1, 1, 1, 0, 2500, 1, 40000),
]

EDITABLE_FIELDS = {
    "spawn_weight", "active_spawn_weight", "shop_weight", "claim_weight",
    "shop_price", "stock_limit", "sell_price",
}

# Live config dicts. Mutated in place (clear + update) by _apply_docs() so
# every module that imported them observes refreshes without re-importing.
RARITY_MAP: dict[int, str] = {}
SPAWN_RARITY_WEIGHTS: dict[str, int] = {}
ACTIVE_SPAWN_RARITY_WEIGHTS: dict[str, int] = {}
SHOP_RARITY_WEIGHTS: dict[str, int] = {}
CLAIM_RARITY_WEIGHTS: dict[str, int] = {}
RARITY_PRICES: dict[str, int] = {}
RARITY_STOCK_LIMITS: dict[str, int] = {}
SELL_PRICES: dict[str, int] = {}  # keyed by bare name ("Common")

_RARITY_DOCS: list[dict] = []


def bare_name(label: str) -> str:
    """'🟢 Medium' -> 'Medium'."""
    return label.split(" ", 1)[1] if " " in label else label


def _default_docs() -> list[dict]:
    return [
        {
            "_id": label, "num": num,
            "spawn_weight": spawn, "active_spawn_weight": active,
            "shop_weight": shop, "claim_weight": claim,
            "shop_price": price, "stock_limit": stock, "sell_price": sell,
        }
        for num, label, spawn, active, shop, claim, price, stock, sell in _DEFAULT_RARITIES
    ]


def _apply_docs(docs: list[dict]) -> None:
    global _RARITY_DOCS
    docs = sorted(docs, key=lambda d: d.get("num", 10**9))
    for target in (RARITY_MAP, SPAWN_RARITY_WEIGHTS, ACTIVE_SPAWN_RARITY_WEIGHTS,
                   SHOP_RARITY_WEIGHTS, CLAIM_RARITY_WEIGHTS, RARITY_PRICES,
                   RARITY_STOCK_LIMITS, SELL_PRICES):
        target.clear()
    for doc in docs:
        label = doc["_id"]
        RARITY_MAP[int(doc.get("num", 0))] = label
        SPAWN_RARITY_WEIGHTS[label] = int(doc.get("spawn_weight", 0))
        ACTIVE_SPAWN_RARITY_WEIGHTS[label] = int(doc.get("active_spawn_weight", 0))
        SHOP_RARITY_WEIGHTS[label] = int(doc.get("shop_weight", 0))
        claim = int(doc.get("claim_weight", 0))
        if claim > 0:
            CLAIM_RARITY_WEIGHTS[label] = claim
        RARITY_PRICES[label] = int(doc.get("shop_price", 5))
        RARITY_STOCK_LIMITS[label] = int(doc.get("stock_limit", 10))
        SELL_PRICES[bare_name(label)] = int(doc.get("sell_price", 50))
    _RARITY_DOCS = docs


def get_rarity_docs() -> list[dict]:
    """Snapshot of the currently loaded rarity docs, sorted by num."""
    return [dict(d) for d in _RARITY_DOCS]


# Import-time fallback so no handler ever sees empty tables; replaced by
# load_rarities() once MongoDB is reachable.
_apply_docs(_default_docs())


async def load_rarities() -> int:
    """Load rarities from DB, seeding from defaults on first startup."""
    from backend.database import rarities_collection
    try:
        docs = await rarities_collection.find({}).to_list(length=1000)
        if not docs:
            try:
                await rarities_collection.insert_many(_default_docs())
            except Exception as e:
                LOGGER.warning("Rarity seed insert failed (%s); re-fetching.", e)
            docs = await rarities_collection.find({}).to_list(length=1000)
        _apply_docs(docs)
        LOGGER.info("Loaded %s rarities from database.", len(docs))
        return len(docs)
    except Exception as e:
        LOGGER.warning("Rarity load from DB failed (%s); using hardcoded defaults.", e)
        return len(_RARITY_DOCS)


async def refresh_rarities() -> int:
    """Re-read the collection into the live dicts. Returns doc count."""
    from backend.database import rarities_collection
    docs = await rarities_collection.find({}).to_list(length=1000)
    _apply_docs(docs)
    return len(docs)


async def set_rarity_field(label: str, field: str, value: int) -> bool:
    """Update one field of a rarity doc and refresh the live dicts."""
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Unknown rarity field: {field}")
    from backend.database import rarities_collection
    result = await rarities_collection.update_one({"_id": label}, {"$set": {field: value}})
    if result.modified_count:
        await refresh_rarities()
    return bool(result.modified_count)


async def add_rarity(num: int, label: str) -> str | None:
    """Add a new rarity. Returns an error message, or None on success."""
    if num in RARITY_MAP:
        return f"Rarity number {num} already exists ({RARITY_MAP[num]})."
    if label in SPAWN_RARITY_WEIGHTS:
        return f"Rarity {label} already exists."
    from backend.database import rarities_collection
    doc = {
        "_id": label, "num": num,
        # Weights start at 0: the rarity stays out of every pool until an
        # admin configures it via /rarityset.
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
