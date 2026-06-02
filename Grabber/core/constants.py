# Grabber/core/constants.py
# Rarity Mappings
SHOP_RARITY = "🟠 Rare"
PAYOUTS = {
    "⚪ Common": 10,
    "🟢 Medium": 25,
    "🟣 Epic": 25,
    "🟠 Rare": 50,
    "🟡 Legendary": 120,
    "💠 Cosmic": 250,
    "🧬 Immortal": 250,
    "💮 Exclusive": 500,
    "🌌 Eternal": 500,
    "🔮 Limited Edition": 750,
    "🔮 Mystic": 750,
    "🫧 Royal": 1500,
    "💎 Antique": 2500,
    "💎 Mythical": 2500,
    "🎐 Celestial": 5000,
    "✨ Divine": 6000,
    "🌠 Astral": 7500,
    "🎞️ AMV": 6000,
    "🪽 Prestige": 7500,
    "❄️ Winter": 500,
    "☀️ Summer": 500,
    "💖 Valentine": 750,
    "🎃 Halloween": 750,
    "💸 Luxury": 500,
    "🎏 Limited": 400
}
# Shop Settings
SHOP_LIMIT = 50
RARITY_PRICES = {
    "⚪ Common": 1,
    "🟢 Medium": 2,
    "🟣 Epic": 2,
    "🟠 Rare": 5,
    "🟡 Legendary": 10,
    "💠 Cosmic": 25,
    "🧬 Immortal": 25,
    "💮 Exclusive": 50,
    "🌌 Eternal": 50,
    "🔮 Limited Edition": 100,
    "🔮 Mystic": 100,
    "🫧 Royal": 250,
    "💎 Antique": 500,
    "💎 Mythical": 500,
    "🎐 Celestial": 1000,
    "✨ Divine": 1500,
    "🌠 Astral": 2500,
    "🎞️ AMV": 1500,
    "🪽 Prestige": 2500,
    "❄️ Winter": 50,
    "☀️ Summer": 50,
    "💖 Valentine": 100,
    "🎃 Halloween": 100,
    "💸 Luxury": 250,
    "🎏 Limited": 200
}

RARITY_STOCK_LIMITS = {
    "⚪ Common": 50,
    "🟢 Medium": 40,
    "🟣 Epic": 40,
    "🟠 Rare": 30,
    "🟡 Legendary": 20,
    "💠 Cosmic": 15,
    "🧬 Immortal": 15,
    "💮 Exclusive": 10,
    "🌌 Eternal": 10,
    "🔮 Limited Edition": 10,
    "🔮 Mystic": 10,
    "🫧 Royal": 5,
    "💎 Antique": 5,
    "💎 Mythical": 5,
    "🎐 Celestial": 2,
    "✨ Divine": 2,
    "🌠 Astral": 1,
    "🎞️ AMV": 2,
    "🪽 Prestige": 1,
    "❄️ Winter": 10,
    "☀️ Summer": 10,
    "💖 Valentine": 10,
    "🎃 Halloween": 10,
    "💸 Luxury": 5,
    "🎏 Limited": 20
}
# Legacy import compatibility. Battle Pass purchases use Telegram Stars (XTR).
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
    "shards": {"label": "Shards", "field": "balance", "icon": "⬪"},
    "zenith": {"label": "Zenith", "field": "zenith", "icon": "⧫"},
    "level": {"label": "Level", "field": "xp", "icon": "◉"},
    "guesses": {"label": "Guesses", "field": "guess_count", "icon": "◎"}
}
