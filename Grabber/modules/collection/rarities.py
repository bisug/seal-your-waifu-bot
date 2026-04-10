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
    "⚪ Common": 50,
    "🟢 Medium": 25,
    "🟠 Rare": 15,
    "🟡 Legendary": 6,
    "💠 Cosmic": 3,
    "💮 Exclusive": 0.8,
    "🔮 Limited Edition": 0.2,
    "🎞️ AMV": 1
}

ACTIVE_RARITY_WEIGHTS = {
    "🟢 Medium": 35,
    "🟠 Rare": 30,
    "🟡 Legendary": 20,
    "💠 Cosmic": 10,
    "💮 Exclusive": 4,
    "🔮 Limited Edition": 1,
    "🎞️ AMV": 2
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
