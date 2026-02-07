from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber.database import collection

RARITY_MAP = {
    1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🪽 Shop", 9: "🫧 Royal", 10: "💎 Antique"
}

@app.on_message(filters.command("rarities"))
async def rarities_handler(_, message: types.Message):
    # Aggregation to count characters by rarity
    pipeline = [
        {"$group": {"_id": "$rarity", "count": {"$sum": 1}}}
    ]
    
    cursor = collection.aggregate(pipeline)
    rarity_counts = {}
    async for doc in cursor:
        rarity_counts[doc["_id"]] = doc["count"]
    
    response = "**Character Counts by Rarity:**\n\n"
    
    # Sort by RARITY_MAP order (keys are 1-10)
    for i in range(1, 11):
        rarity_name = RARITY_MAP.get(i)
        if rarity_name:
            count = rarity_counts.get(rarity_name, 0)
            response += f"{rarity_name}: `{count}`\n"
    
    await message.reply_text(response, parse_mode=enums.ParseMode.MARKDOWN)
