from pyrogram import filters, enums, types
from pyrogram.enums import ParseMode
from Grabber.core.utils import md_escape
from Grabber import app
from Grabber.database import user_collection

                                            
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
            parse_mode=ParseMode.MARKDOWN
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
    
                            
    new_shards = current_shards - shards_amount
    current_zenith = user.get("zenith", 0) if user else 0
    new_zenith = current_zenith + zenith_amount
    
                                       
    confirmation_text = (
        f"💱 **Exchange Confirmation**\n\n"
        f"**Converting:** {shards_amount:,} ⬪ → {zenith_amount:,} ⧫\n\n"
        f"**Current Balance:**\n"
        f"Shards: {current_shards:,} ⬪\n"
        f"Zenith: {current_zenith:,} ⧫\n\n"
        f"**New Balance:**\n"
        f"Shards: {new_shards:,} ⬪\n"
        f"Zenith: {new_zenith:,} ⧫\n\n"
        f"_Proceed with exchange?_"
    )
    
    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"exchange_confirm_{shards_amount}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="exchange_cancel")
        ]
    ]
    
    await message.reply_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

                       
@app.on_callback_query(filters.regex(r"^exchange_confirm_(\d+)$"))
async def exchange_confirm_callback(_, query: types.CallbackQuery):
    shards_amount = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    user = await user_collection.find_one({"id": user_id})
    current_shards = user.get("balance", 0) if user else 0
    
                        
    if current_shards < shards_amount:
        await query.answer("❌ Insufficient Shards!", show_alert=True)
        return
    
    zenith_amount = shards_amount // 10000
    
                      
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
    
                            
    new_shards = current_shards - shards_amount
    current_zenith = user.get("zenith", 0) if user else 0
    new_zenith = current_zenith + zenith_amount
    
    await query.message.edit_text(
        f"✅ **Exchange Successful!**\n\n"
        f"Converted: {shards_amount:,} ⬪ → {zenith_amount:,} ⧫\n\n"
        f"**Your New Balance:**\n"
        f"Shards: {new_shards:,} ⬪\n"
        f"Zenith: {new_zenith:,} ⧫",
        parse_mode=ParseMode.MARKDOWN
    )
    await query.answer("Exchange completed!")

                 
@app.on_callback_query(filters.regex(r"^exchange_cancel$"))
async def exchange_cancel_callback(_, query: types.CallbackQuery):
    await query.message.edit_text(
        "❌ **Exchange Cancelled**\n\n"
        "Your balance remains unchanged.",
        parse_mode=ParseMode.MARKDOWN
    )
    await query.answer("Cancelled")
