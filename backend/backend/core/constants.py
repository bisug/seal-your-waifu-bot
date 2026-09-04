# backend/core/constants.py
from pyrogram import errors

# Kurigram 2.2.25 (#357): ChatWriteForbidden et al. are BadRequest now.
# Catch this tuple *before* any `except errors.BadRequest`.
PERMISSION_DENIED_ERRORS = (
    errors.Forbidden,
    errors.Unauthorized,
    errors.ChatWriteForbidden,
    errors.ChatAdminRequired,
    errors.ChannelPrivate,
)

# Rarity Mappings
SHOP_RARITY = "🟠 Rare"
# Shop Settings
SHARDS_PER_ZENITH = 10_000
LEVEL_BUY_SHARD_COST = SHARDS_PER_ZENITH
SHOP_LIMIT = 50
# Per-rarity pricing/stock live in the `rarities` collection (core/rarities.py).
from backend.core.rarities import RARITY_PRICES, RARITY_STOCK_LIMITS  # noqa: E402,F401

# Battle Pass purchases use Telegram Stars (XTR).
PASS_PRICES = {
    "premium": 24,
    "elite": 49
}
# Eggs
CORRUPTED_EGG_CHANCE = 5
EGG_TIERS = {
    "common": {"name": "Common Egg", "chance": 58.0, "pool": ["⚪ Common", "🟢 Medium"], "wait_min": 4, "rank": 0},
    "gold": {"name": "Golden Egg", "chance": 30.0, "pool": ["🟠 Rare", "🟡 Legendary"], "wait_min": 20, "rank": 1},
    "void": {"name": "Void Egg", "chance": 8.5, "pool": ["💠 Cosmic", "🧬 Immortal", "💮 Exclusive"], "wait_min": 75, "rank": 2},
    "rare": {"name": "Rare Egg", "chance": 2.4, "pool": ["🟠 Rare", "🟡 Legendary", "💠 Cosmic", "🧬 Immortal"], "wait_min": 120, "rank": 3},
    "legendary": {"name": "Legendary Egg", "chance": 0.9, "pool": ["💮 Exclusive", "🌌 Eternal", "🫧 Royal", "💎 Mythical"], "wait_min": 240, "rank": 4},
    "celestial": {"name": "Celestial Egg", "chance": 0.2, "pool": ["🎐 Celestial", "✨ Divine", "🌠 Astral", "🪽 Prestige"], "wait_min": 420, "rank": 5}
}
# Leaderboard Metrics
METRIC_ORDER = ["harem", "shards", "zenith", "level", "guesses"]
METRICS = {
    "harem": {"label": "Harem", "field": "char_count", "icon": "◈"},
    "shards": {"label": "Coins", "field": "balance", "icon": "🪙"},
    "zenith": {"label": "Prisms", "field": "zenith", "icon": "💠"},
    "level": {"label": "Level", "field": "xp", "icon": "◉"},
    "guesses": {"label": "Guesses", "field": "guess_count", "icon": "◎"}
}
