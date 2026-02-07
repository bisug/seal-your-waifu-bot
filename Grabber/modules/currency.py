from datetime import datetime, timezone
from pyrogram import filters, enums, types
from Grabber.app import app
from Grabber.database import user_collection

# Exchange command: Convert Shards to Zenith
@app.on_message(filters.command("exchange"))
async def exchange_command(_, message: types.Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        return await message.reply_text(
            "💱 **Shards → Zenith Exchange**\n\n"
            "**Usage:** `/exchange <amount>`\n"
            "**Example:** `/exchange 50000`\n\n"
            "**Rate:** 10,000 ⬪ = 1 ⧫\n"
            "**Minimum:** 10,000 Shards",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    
    try:
        shards_amount = int(message.command[1].replace(",", ""))
    except ValueError:
        return await message.reply_text("❌ Invalid amount. Please enter a number.")
    
    if shards_amount < 10000:
        return await message.reply_text(f"❌ Minimum exchange is 10,000 ⬪ Shards (= 1 ⧫ Zenith).")
    
    if shards_amount % 10000 != 0:
        return await message.reply_text(f"❌ Amount must be divisible by 10,000 ⬪.")
    
    user = await user_collection.find_one({"id": user_id})
    current_shards = user.get("balance", 0) if user else 0
    
    if current_shards < shards_amount:
        return await message.reply_text(
            f"❌ Insufficient Shards!\n\n"
            f"You have: {current_shards:,} ⬪\n"
            f"Need: {shards_amount:,} ⬪"
        )
    
    zenith_amount = shards_amount // 10000
    
    # Perform exchange
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {
                "balance": -shards_amount,
                "zenith": zenith_amount
            }
        },
        upsert=True
    )
    
    await message.reply_text(
        f"✅ **Exchange Successful!**\n\n"
        f"Converted: {shards_amount:,} ⬪ → {zenith_amount:,} ⧫\n\n"
        f"Use `/balance` to check your new balance!",
        parse_mode=enums.ParseMode.MARKDOWN
    )
