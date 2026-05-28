from pyrogram import enums, filters, types

from Grabber import app
from Grabber.core.utils import handle_errors
from Grabber.database import collection

# Keep for backward compatibility/reference
RARITY_MAP = {
    1: "⚪ Common", 2: "🟢 Medium", 3: "🟠 Rare", 4: "🟡 Legendary", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🫧 Royal", 9: "💎 Antique", 10: "🎐 Celestial",
    11: "🎞️ AMV", 12: "🪽 Prestige", 13: "❄️ Winter", 14: "☀️ Summer", 15: "💖 Valentine",
    16: "🎃 Halloween", 17: "💸 Luxury", 18: "🎏 Limited", 19: "🟣 Epic", 20: "🧬 Immortal",
    21: "🌌 Eternal", 22: "🔮 Mystic", 23: "💎 Mythical", 24: "✨ Divine", 25: "🌠 Astral"
}
RARITY_WEIGHTS = {
    "⚪ Common": 25,
    "🟢 Medium": 20,
    "🟠 Rare": 15,
    "🟡 Legendary": 10,
    "💠 Cosmic": 8,
    "💮 Exclusive": 6,
    "🔮 Limited Edition": 5,
    "🫧 Royal": 4,
    "💎 Antique": 3,
    "🎐 Celestial": 2,
    "🎞️ AMV": 2,
    "🪽 Prestige": 1,
    "❄️ Winter": 6,
    "☀️ Summer": 6,
    "💖 Valentine": 5,
    "🎃 Halloween": 5,
    "💸 Luxury": 4,
    "🎏 Limited": 10,
    "🟣 Epic": 20,
    "🧬 Immortal": 8,
    "🌌 Eternal": 6,
    "🔮 Mystic": 5,
    "💎 Mythical": 3,
    "✨ Divine": 2,
    "🌠 Astral": 1
}
ACTIVE_RARITY_WEIGHTS = {
    "🟠 Rare": 20,
    "🟡 Legendary": 15,
    "💠 Cosmic": 15,
    "💮 Exclusive": 12,
    "🔮 Limited Edition": 10,
    "🫧 Royal": 8,
    "💎 Antique": 7,
    "🎐 Celestial": 6,
    "🎞️ AMV": 7,
    "🪽 Prestige": 3,
    "❄️ Winter": 12,
    "☀️ Summer": 12,
    "💖 Valentine": 10,
    "🎃 Halloween": 10
}
@app.on_message(filters.command("rarities"))
@handle_errors
async def rarities_handler(_, message: types.Message):
    pipeline = [
        {"$group": {"_id": "$rarity", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    # Under PyMongo 4.17+ native AsyncMongoClient, aggregate() is a coroutine
    cursor = await collection.aggregate(pipeline)

    rarity_counts = {}
    total_characters = 0

    async for doc in cursor:
        r_id = doc["_id"] or "Unknown"
        rarity_counts[r_id] = doc["count"]
        total_characters += doc["count"]

    if not rarity_counts:
        return await message.reply_text("<b>No characters found in database.</b>", parse_mode=enums.ParseMode.HTML)

    response = "<b>Character Counts by Rarity:</b>\n\n"

    # We display based on what's in the database, but prioritized by RARITY_MAP order if possible
    displayed_rarities = set()

    # 1. Show standard rarities first
    for i in sorted(RARITY_MAP.keys()):
        rarity_name = RARITY_MAP[i]
        if rarity_name in rarity_counts:
            count = rarity_counts[rarity_name]
            response += f"{rarity_name}: <code>{count}</code>\n"
            displayed_rarities.add(rarity_name)

    # 2. Show any remaining rarities found in DB
    remaining = False
    for r_name, count in rarity_counts.items():
        if r_name not in displayed_rarities:
            if not remaining:
                response += "\n<b>Other Rarities:</b>\n"
                remaining = True
            response += f"{r_name}: <code>{count}</code>\n"

    response += f"\n<b>Total Characters:</b> <code>{total_characters}</code>\n"
    await message.reply_text(response, parse_mode=enums.ParseMode.HTML)
