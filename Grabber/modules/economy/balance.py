import asyncio
import random
from datetime import datetime, timezone
from pyrogram import filters, enums, types
from pyrogram.enums import ButtonStyle, ParseMode
from Grabber.core.utils import html_escape
from Grabber import app
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
        f"💳 <b>Your Balance</b>\n\n"
        f"<b>Shards:</b> {shards:,} ⬪\n"
        f"<b>Zenith:</b> {zenith:,} ⧫\n\n"
        f"<i>Exchange: 10,000 ⬪ = 1 ⧫</i>\n"
        f"<i>Use <code>/exchange</code> to convert Shards to Zenith</i>"
    )

    await message.reply_text(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("pay") & filters.reply)
async def pay_cmd(_, message: types.Message):
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name
    recipient = message.reply_to_message.from_user
    recipient_id = recipient.id

    if recipient_id == sender_id:
        return await message.reply_text("❌ <b>You cannot pay yourself.</b>", parse_mode=ParseMode.HTML)

    try:
        amount = int(message.command[1])
        if amount <= 0: raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("❌ <b>Usage:</b> <code>/pay &lt;amount&gt;</code> (reply to user)", parse_mode=ParseMode.HTML)

    balance = await get_user_balance(sender_id)
    if balance < amount:
        return await message.reply_text("❌ <b>Insufficient balance!</b>", parse_mode=ParseMode.HTML)

    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"pay_c_{recipient_id}_{amount}_{sender_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"pay_a_{sender_id}")
        ]
    ]

    await message.reply_text(
        f"<b>💸 Payment Confirmation</b>\n\n"
        f'<b>To:</b> <a href="tg://user?id={recipient.id}">{html_escape(recipient.first_name)}</a>\n'
        f"<b>Amount:</b> {amount:,} ⬪\n\n"
        f"<i>Are you sure you want to send these Shards?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^pay_"))
async def pay_callback_handler(_, query: types.CallbackQuery):
    sender_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]

    # Handle payment cancellation
    if action == "a":
        owner_id = int(data[2]) if len(data) > 2 else 0
        if owner_id and sender_id != owner_id:
            return await query.answer("❌ This is not your payment!", show_alert=True)
        await query.message.edit_text("❌ <b>Payment cancelled.</b>", parse_mode=ParseMode.HTML)
        return

    recipient_id = int(data[2])
    amount = int(data[3])
    owner_id = int(data[4]) if len(data) > 4 else 0

    if owner_id and sender_id != owner_id:
        return await query.answer("❌ This is not your payment!", show_alert=True)


    if await check_and_deduct(sender_id, amount):
        await update_user_balance(recipient_id, amount)


        try:
            recipient = await app.get_users(recipient_id)
            mention = f'<a href="tg://user?id={recipient.id}">{html_escape(recipient.first_name)}</a>'
        except Exception:
            mention = f"User ID: {recipient_id}"

        await query.message.edit_text(
            f"✅ <b>Payment Successful!</b>\n\n"
            f"<b>Sent:</b> {amount:,} ⬪\n"
            f"<b>To:</b> {mention}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.answer("❌ Insufficient balance or transaction failed.", show_alert=True)




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

    lines = [f"{i+1}. {html_escape(u.get('first_name', 'User'))} - 💵 {u.get('balance', 0)}" for i, u in enumerate(top_users)]
    await message.reply_text("🏆 <b>Top 10 Rich Users</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)
