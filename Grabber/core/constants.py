# Grabber/core/constants.py
# Rarity Mappings
SHOP_RARITY = "🟠 Rare"
PAYOUTS = {
    "⚪ Common": 10,
    "🟢 Medium": 25,
    "🟠 Rare": 50,
    "🟡 Legendary": 120,
    "💠 Cosmic": 250,
    "💮 Exclusive": 500,
    "🔮 Limited Edition": 750,
    "🫧 Royal": 1500,
    "💎 Antique": 2500,
    "🎐 Celestial": 5000,
    "❄️ Winter": 500,
    "☀️ Summer": 500,
    "💖 Valentine": 750,
    "🎃 Halloween": 750
}
# Shop Settings
SHOP_LIMIT = 50
RARITY_PRICES = {
    "⚪ Common": 1,
    "🟢 Medium": 2,
    "🟠 Rare": 5,
    "🟡 Legendary": 10,
    "💠 Cosmic": 25,
    "💮 Exclusive": 50,
    "🔮 Limited Edition": 100,
    "🫧 Royal": 250,
    "💎 Antique": 500,
    "🎐 Celestial": 1000,
    "🎞️ AMV": 1500,
    "🪽 Prestige": 2500,
    "❄️ Winter": 50,
    "☀️ Summer": 50,
    "💖 Valentine": 100,
    "🎃 Halloween": 100
}

RARITY_STOCK_LIMITS = {
    "⚪ Common": 50,
    "🟢 Medium": 40,
    "🟠 Rare": 30,
    "🟡 Legendary": 20,
    "💠 Cosmic": 15,
    "💮 Exclusive": 10,
    "🔮 Limited Edition": 10,
    "🫧 Royal": 5,
    "💎 Antique": 5,
    "🎐 Celestial": 2,
    "🎞️ AMV": 2,
    "🪽 Prestige": 1,
    "❄️ Winter": 10,
    "☀️ Summer": 10,
    "💖 Valentine": 10,
    "🎃 Halloween": 10
}
# Pass Constants
PASS_PRICES = {
    "premium": 500,
    "elite": 1200
}
# Eggs
CORRUPTED_EGG_CHANCE = 5
EGG_TIERS = {
    "common": {"name": "Common Egg", "chance": 70, "pool": ["⚪ Common", "🟢 Medium"], "wait_min": 5},
    "gold":   {"name": "Golden Egg", "chance": 25, "pool": ["🟠 Rare", "🟡 Legendary"], "wait_min": 30},
    "void":   {"name": "Void Egg",   "chance": 5,  "pool": ["💠 Cosmic", "💮 Exclusive"], "wait_min": 180}
}
# Leaderboard Metrics
METRIC_ORDER = ["harem", "shards", "zenith", "level", "guesses"]
METRICS = {
    "harem": {"label": "Harem", "field": "char_count", "icon": "◈"},
    "shards": {"label": "Shards", "field": "balance", "icon": "⬪"},
    "zenith": {"label": "Zenith", "field": "zenith", "icon": "⧫"},
    "level": {"label": "Level", "field": "xp", "icon": "◉"},
    "guesses": {"label": "Guesses", "field": "guess_count", "icon": "◎"}
}
