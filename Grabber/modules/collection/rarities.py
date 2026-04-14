from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app
from Grabber.database import collection

RARITY_MAP = {
    1: "⚪ Common", 2: "🟢 Medium", 3: "🟠 Rare", 4: "🟡 Legendary", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🫧 Royal", 9: "💎 Antique", 10: "🎐 Celestial",
    11: "🎞️ AMV"
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
    "🎞️ AMV": 2
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
    "🎞️ AMV": 7
}

@app.on_message(filters.command("rarities"))
async def rarities_handler(_, message: types.Message):

    pipeline = [
        {"$group": {"_id": "$rarity", "count": {"$sum": 1}}}
    ]

    cursor = collection.aggregate(pipeline)
    rarity_counts = {}
    async for doc in cursor:
        rarity_counts[doc["_id"]] = doc["count"]

    response = "<b>Character Counts by Rarity:</b>\n\n"


    for i in range(1, 11):
        rarity_name = RARITY_MAP.get(i)
        if rarity_name:
            count = rarity_counts.get(rarity_name, 0)
            response += f"{rarity_name}: <code>{count}</code>\n"

    await message.reply_text(response, parse_mode=ParseMode.HTML)
