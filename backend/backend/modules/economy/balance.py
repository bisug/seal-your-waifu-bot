import uuid
from pyrogram import enums, filters, types

from backend import LOGGER, app
from backend.core.balance import (check_and_deduct, get_user_balance,
                                  update_user_balance)
from backend.core.cache import invalidate_user_cache
from backend.core.sessions import consume_session, create_session, delete_session, get_session
from backend.core.user import get_user_filter
from backend.core.utils import handle_errors, html_escape
from backend.database import user_collection
@app.on_message(filters.command(["balance", "bal"]))
@handle_errors
async def balance_cmd(_, message: types.Message):
    """Retrieve and display the user's Shards and Zenith balance."""
    user_id = message.from_user.id
    user = await user_collection.find_one(get_user_filter(user_id))
    if not user:
        shards = 0
        zenith = 0
    else:
        shards = user.get("balance", 0)
        zenith = user.get("zenith", 0)
    text = (
        f"<b>Your Balance</b>\n\n"
        f"<b>Shards:</b> {shards:,} ⬪\n"
        f"<b>Zenith:</b> {zenith:,} ⧫\n\n"
        f"<i>Use <code>/zenith</code> or <code>/shard</code> to exchange currency.</i>"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("pay") & filters.reply)
@handle_errors
async def pay_cmd(_, message: types.Message):
    """Initiate a Shard payment to another user via reply."""
    sender_id = message.from_user.id
    recipient = message.reply_to_message.from_user
    if not recipient:
        return await message.reply_text("<b>Cannot pay this message (no user attached).</b>", parse_mode=enums.ParseMode.HTML)
    recipient_id = recipient.id
    if recipient_id == sender_id:
        return await message.reply_text("<b>You cannot pay yourself.</b>", parse_mode=enums.ParseMode.HTML)
    try:
        amount = int(message.command[1])
        if amount <= 0: raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("<b>Usage:</b> <code>/pay &lt;amount&gt;</code> (reply to user)", parse_mode=enums.ParseMode.HTML)
    balance = await get_user_balance(sender_id)
    if balance < amount:
        return await message.reply_text("<b>Insufficient balance!</b>", parse_mode=enums.ParseMode.HTML)
    payment_id = f"pay_{uuid.uuid4().hex}"
    await create_session(payment_id, {
        "sender": sender_id,
        "recipient": recipient_id,
        "amount": amount,
    }, ttl=600)
    buttons = [
        [
            types.InlineKeyboardButton("Confirm", callback_data=f"pay:c:{payment_id}"),
            types.InlineKeyboardButton("Cancel", callback_data=f"pay:a:{payment_id}")
        ]
    ]
    await message.reply_text(
        f"<b>Payment Confirmation</b>\n\n"
        f'<b>To:</b> <a href="tg://user?id={recipient.id}">{html_escape(recipient.first_name)}</a>\n'
        f"<b>Amount:</b> {amount:,} ⬪\n\n"
        f"<i>Are you sure you want to send these Shards?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^pay[:_]"))
async def pay_callback_handler(_, query: types.CallbackQuery):
    """Handle the confirmation or cancellation of a payment."""
    sender_id = query.from_user.id
    if ":" not in query.data:
        return await query.answer("This payment confirmation has expired. Use /pay again.", show_alert=True)

    data = query.data.split(":")
    action = data[1]
    payment_id = data[2] if len(data) > 2 else ""
    payment_info = await get_session(payment_id)
    if not payment_info:
        return await query.answer("This payment expired or was already handled.", show_alert=True)
    owner_id = int(payment_info["sender"])
    if sender_id != owner_id:
        return await query.answer("This is not your payment!", show_alert=True)

    # Handle payment cancellation
    if action == "a":
        await delete_session(payment_id)
        await query.message.edit_text("<b>Payment cancelled.</b>", parse_mode=enums.ParseMode.HTML)
        return

    if action != "c":
        return await query.answer("Invalid payment action.", show_alert=True)
    payment_info = await consume_session(payment_id)
    if not payment_info:
        return await query.answer("This payment expired or was already handled.", show_alert=True)
    if sender_id != int(payment_info["sender"]):
        return await query.answer("This is not your payment!", show_alert=True)

    recipient_id = int(payment_info["recipient"])
    amount = int(payment_info["amount"])
    if await check_and_deduct(sender_id, amount):
        try:
            await update_user_balance(recipient_id, amount)
        except Exception as e:
            # Sender was already debited — refund so a failed credit never
            # destroys shards.
            LOGGER.error(f"Payment credit failed {sender_id} -> {recipient_id}: {e}")
            try:
                await update_user_balance(sender_id, amount)
            except Exception:
                LOGGER.exception(f"CRITICAL: payment refund failed for {sender_id}")
            return await query.answer("Payment failed. Your Shards were returned.", show_alert=True)
        try:
            recipient = await app.get_users(recipient_id)
            mention = f'<a href="tg://user?id={recipient.id}">{html_escape(recipient.first_name)}</a>'
        except Exception:
            mention = f"User ID: {recipient_id}"
        await query.message.edit_text(
            f"<b>Payment Successful!</b>\n\n"
            f"<b>Sent:</b> {amount:,} ⬪\n"
            f"<b>To:</b> {mention}",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.answer("Insufficient balance or transaction failed.", show_alert=True)
@app.on_message(filters.command("bonus"))
@handle_errors
async def bonus_cmd(_, message: types.Message):
    user_id = message.from_user.id
    # Atomic claim: the $ne guard turns the read-then-write into a single
    # conditional update so concurrent /bonus calls can't both grant.
    result = await user_collection.update_one(
        {**get_user_filter(user_id), "bonus_claimed": {"$ne": True}},
        {"$inc": {"balance": 3000}, "$set": {"bonus_claimed": True}},
        upsert=True,
    )
    if result.modified_count == 0 and result.upserted_id is None:
        return await message.reply_text("Already claimed, stay tuned!")
    await invalidate_user_cache(user_id)
    await message.reply_text("You've claimed 3000 ⬪!")
@app.on_message(filters.command("mtop"))
@handle_errors
async def mtop_cmd(_, message: types.Message):
    cursor = user_collection.find({}, {"id": 1, "first_name": 1, "last_name": 1, "balance": 1}).sort("balance", -1).limit(10)
    top_users = await cursor.to_list(length=10)

    from backend.modules.info.leaderboard import _resolve_missing_names
    top_users = await _resolve_missing_names(top_users)

    lines = []
    for i, u in enumerate(top_users):
        uid = u.get("id")
        first_name = u.get('first_name', 'User')
        last_name = u.get('last_name')
        full_name = f"{first_name} {last_name}" if last_name else first_name
        mention = f'<a href="tg://user?id={uid}">{html_escape(full_name)}</a>'
        balance = u.get('balance', 0)
        lines.append(f"{i+1}. {mention} - <b>{balance:,} ⬪</b>")

    await message.reply_text("<b>Top 10 Rich Users</b>\n\n" + "\n".join(lines), parse_mode=enums.ParseMode.HTML)
