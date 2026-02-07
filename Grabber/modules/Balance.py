import asyncio
import random
from datetime import datetime, timezone
from pyrogram import filters, enums, types
from Grabber.app import app
from Grabber import collection, OWNER_ID, SUPPORT_GROUP_ID, LOGGER
from Grabber.core.game import get_user_balance, update_user_balance, check_and_deduct
from Grabber.database import user_collection

@app.on_message(filters.command(["balance", "bal"]))
async def balance_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    
    if not user:
        shards = 0
        zenith = 0
    else:
        shards = user.get("balance", 0)
        zenith = user.get("zenith", 0)
    
    text = (
        f"💳 **Your Balance**\n\n"
        f"**Shards:** {shards:,} ⬪\n"
        f"**Zenith:** {zenith:,} ⧫\n\n"
        f"_Exchange: 10,000 ⬪ = 1 ⧫_\n"
        f"_Use /exchange to convert Shards to Zenith_"
    )
    
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("pay") & filters.reply)
async def pay_cmd(_, message: types.Message):
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    recipient = message.reply_to_message.from_user
    recipient_id = recipient.id

    if recipient_id == sender_id:
        return await message.reply_text("❌ **You cannot pay yourself.**", parse_mode=enums.ParseMode.MARKDOWN)

    try:
        amount = int(message.command[1])
        if amount <= 0: raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("❌ **Usage:** `/pay <amount>` (reply to user)", parse_mode=enums.ParseMode.MARKDOWN)

    balance = await get_user_balance(sender_id)
    if balance < amount:
        return await message.reply_text("❌ **Insufficient balance!**", parse_mode=enums.ParseMode.MARKDOWN)

    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"pay_c_{recipient_id}_{amount}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="pay_a")
        ]
    ]

    await message.reply_text(
        f"**💸 Payment Confirmation**\n\n"
        f"**To:** {recipient.mention}\n"
        f"**Amount:** {amount:,} ⬪\n\n"
        f"_Are you sure you want to send these Shards?_",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_callback_query(filters.regex(r"^pay_"))
async def pay_callback_handler(_, query: types.CallbackQuery):
    sender_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]

    if action == "a":
        await query.message.edit_text("❌ **Payment cancelled.**", parse_mode=enums.ParseMode.MARKDOWN)
        return

    recipient_id = int(data[2])
    amount = int(data[3])

    # Atomic check and deduct
    if await check_and_deduct(sender_id, amount):
        await update_user_balance(recipient_id, amount)
        
        # Get user info for better message
        try:
            recipient = await app.get_users(recipient_id)
            mention = recipient.mention
        except Exception:
            mention = f"User ID: {recipient_id}"

        await query.message.edit_text(
            f"✅ **Payment Successful!**\n\n"
            f"**Sent:** {amount:,} ⬪\n"
            f"**To:** {mention}",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await query.answer("❌ Insufficient balance or transaction failed.", show_alert=True)

@app.on_message(filters.command("daily"))
async def daily_reward_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({"id": user_id}, {"last_daily_reward": 1})

    today = datetime.now(timezone.utc).date()
    if user_data and user_data.get("last_daily_reward"):
        last_daily = user_data["last_daily_reward"]
        if hasattr(last_daily, 'date') and last_daily.date() == today:
            return await message.reply_text("❌ Already claimed today!")

    await update_user_balance(user_id, 150)
    await user_collection.update_one({"id": user_id}, {"$set": {"last_daily_reward": datetime.now(timezone.utc)}})
    await message.reply_text("🎉 Claimed 150 ⬪!")

@app.on_message(filters.command("bonus"))
async def bonus_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}, {"bonus_claimed": 1})

    if user and user.get("bonus_claimed"):
        return await message.reply_text("❌ Already claimed stay tuned!")

    await update_user_balance(user_id, 3000)
    await user_collection.update_one({"id": user_id}, {"$set": {"bonus_claimed": True}})
    await message.reply_text("🎁 You've claimed 3000 ⬪!")

@app.on_message(filters.command("mtop"))
async def mtop_cmd(_, message: types.Message):
    cursor = user_collection.find({}, {"id": 1, "first_name": 1, "balance": 1}).sort("balance", -1).limit(10)
    top_users = await cursor.to_list(length=10)
    
    lines = [f"{i+1}. {u.get('first_name', 'User')} - 💵 {u.get('balance', 0)}" for i, u in enumerate(top_users)]
    await message.reply_text("🏆 **Top 10 Rich Users**\n\n" + "\n".join(lines))
