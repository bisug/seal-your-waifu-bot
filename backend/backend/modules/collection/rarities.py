from pyrogram import enums, filters, types

from backend import app
from backend.core.utils import handle_errors, html_escape
from backend.database import collection

# Keep for backward compatibility/reference
RARITY_MAP = {
    1: "⚪ Common", 2: "🟢 Medium", 3: "🟠 Rare", 4: "🟡 Legendary", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🫧 Royal", 9: "💎 Antique", 10: "🎐 Celestial",
    11: "🎞️ AMV", 12: "🪽 Prestige", 13: "❄️ Winter", 14: "☀️ Summer", 15: "💖 Valentine",
    16: "🎃 Halloween", 17: "💸 Luxury", 18: "🎏 Limited", 19: "🟣 Epic", 20: "🧬 Immortal",
    21: "🌌 Eternal", 22: "🔮 Mystic", 23: "💎 Mythical", 24: "✨ Divine", 25: "🌠 Astral"
}
SPAWN_RARITY_WEIGHTS = {
    "⚪ Common": 360,
    "🟢 Medium": 240,
    "🟣 Epic": 120,
    "🟠 Rare": 110,
    "🟡 Legendary": 50,
    "💠 Cosmic": 25,
    "🧬 Immortal": 25,
    "🎏 Limited": 18,
    "❄️ Winter": 12,
    "☀️ Summer": 12,
    "💸 Luxury": 8,
    "💖 Valentine": 5,
    "🎃 Halloween": 5,
    "💮 Exclusive": 4,
    "🌌 Eternal": 3,
    "🔮 Limited Edition": 2,
    "🔮 Mystic": 2,
    "🫧 Royal": 1,
    "💎 Antique": 1,
    "💎 Mythical": 1,
    "🎐 Celestial": 1,
    "✨ Divine": 1,
    "🎞️ AMV": 1,
    "🪽 Prestige": 1,
    "🌠 Astral": 1,
}
ACTIVE_SPAWN_RARITY_WEIGHTS = {
    "⚪ Common": 280,
    "🟢 Medium": 220,
    "🟣 Epic": 140,
    "🟠 Rare": 130,
    "🟡 Legendary": 70,
    "💠 Cosmic": 35,
    "🧬 Immortal": 35,
    "🎏 Limited": 25,
    "❄️ Winter": 15,
    "☀️ Summer": 15,
    "💸 Luxury": 12,
    "💖 Valentine": 8,
    "🎃 Halloween": 8,
    "💮 Exclusive": 6,
    "🌌 Eternal": 4,
    "🔮 Limited Edition": 3,
    "🔮 Mystic": 3,
    "🫧 Royal": 2,
    "💎 Antique": 2,
    "💎 Mythical": 2,
    "🎐 Celestial": 1,
    "✨ Divine": 1,
    "🎞️ AMV": 1,
    "🪽 Prestige": 1,
    "🌠 Astral": 1,
}
SHOP_RARITY_WEIGHTS = {
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
    "🌠 Astral": 1,
}
RARITY_WEIGHTS = SPAWN_RARITY_WEIGHTS
ACTIVE_RARITY_WEIGHTS = ACTIVE_SPAWN_RARITY_WEIGHTS
@app.on_message(filters.command(["rarities", "rarity", "rlist"]))
@handle_errors
async def rarities_handler(_, message: types.Message):
    rarity_counts = {}
    total_characters = 0

    cursor = collection.find({}, {"rarity": 1})
    async for doc in cursor:
        rarity = doc.get("rarity") or "Unknown"
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        total_characters += 1

    if not rarity_counts:
        return await message.reply_text("<b>No characters found in database.</b>", parse_mode=enums.ParseMode.HTML)

    lines = ["<b>Character Counts by Rarity:</b>", ""]

    # We display based on what's in the database, but prioritized by RARITY_MAP order if possible
    displayed_rarities = set()

    # 1. Show standard rarities first
    for i in sorted(RARITY_MAP.keys()):
        rarity_name = RARITY_MAP[i]
        if rarity_name in rarity_counts:
            count = rarity_counts[rarity_name]
            lines.append(f"{html_escape(rarity_name)}: <code>{count}</code>")
            displayed_rarities.add(rarity_name)

    # 2. Show any remaining rarities found in DB
    remaining = False
    for r_name, count in rarity_counts.items():
        if r_name not in displayed_rarities:
            if not remaining:
                lines.extend(["", "<b>Other Rarities:</b>"])
                remaining = True
            lines.append(f"{html_escape(str(r_name))}: <code>{count}</code>")

    lines.extend(["", f"<b>Total Characters:</b> <code>{total_characters}</code>"])

    chunk = ""
    for line in lines:
        next_chunk = f"{chunk}\n{line}" if chunk else line
        if len(next_chunk) > 3500:
            await message.reply_text(chunk, parse_mode=enums.ParseMode.HTML)
            chunk = line
        else:
            chunk = next_chunk
    if chunk:
        await message.reply_text(chunk, parse_mode=enums.ParseMode.HTML)
