from pyrogram import filters, types, enums
from Grabber import app, user_collection, OWNER_ID, sudo_users

AUTHORIZED_CONSOLES = set(sudo_users + [OWNER_ID])

async def get_target_user(message: types.Message):
    """Helper to get user_id and amount from a command (ID/Reply)."""
    if message.reply_to_message:
        try:
            amount = int(message.command[1])
            return message.reply_to_message.from_user.id, amount, message.reply_to_message.from_user.first_name
        except (IndexError, ValueError):
            return None, None, None
    else:
        try:
            target_id = int(message.command[1])
            amount = int(message.command[2])
            # Try to get user name
            try:
                user = await app.get_users(target_id)
                name = user.first_name
            except Exception:
                name = f"ID: {target_id}"
            return target_id, amount, name
        except (IndexError, ValueError):
            return None, None, None

@app.on_message(filters.command("givecoin"))
async def give_coin_handler(_, message: types.Message):
    if message.from_user.id not in AUTHORIZED_CONSOLES:
        return await message.reply_text("❌ <b>Unauthorized. Only for Admins.</b>", parse_mode=enums.ParseMode.HTML)

    user_id, amount, name = await get_target_user(message)
    if not user_id or amount <= 0:
        return await message.reply_text(
            "❌ <b>Invalid Format!</b>\n\n"
            "1️⃣ <b>Reply:</b> <code>/givecoin &lt;amount&gt;</code>\n"
            "2️⃣ <b>Direct:</b> <code>/givecoin &lt;user_id&gt; &lt;amount&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )

    buttons = [[
        types.InlineKeyboardButton("✅ Confirm Give", callback_data=f"admin_coin_give_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="admin_coin_cancel")
    ]]

    await message.reply_text(
        f"<b>🏦 Admin Transfer</b>\n\n"
        f"<b>Action:</b> GIVING Coins\n"
        f"<b>Target:</b> {name}\n"
        f"<b>Amount:</b> 💵 <code>{amount:,}</code> coins\n\n"
        "<i>Confirm this action?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@app.on_message(filters.command("takecoin"))
async def take_coin_handler(_, message: types.Message):
    if message.from_user.id not in AUTHORIZED_CONSOLES:
        return await message.reply_text("❌ <b>Unauthorized. Only for Admins.</b>", parse_mode=enums.ParseMode.HTML)

    user_id, amount, name = await get_target_user(message)
    if not user_id or amount <= 0:
        return await message.reply_text(
            "❌ <b>Invalid Format!</b>\n\n"
            "1️⃣ <b>Reply:</b> <code>/takecoin &lt;amount&gt;</code>\n"
            "2️⃣ <b>Direct:</b> <code>/takecoin &lt;user_id&gt; &lt;amount&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )

    buttons = [[
        types.InlineKeyboardButton("✅ Confirm Take", callback_data=f"admin_coin_take_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="admin_coin_cancel")
    ]]

    await message.reply_text(
        f"<b>🏦 Admin Deduction</b>\n\n"
        f"<b>Action:</b> TAKING Coins\n"
        f"<b>Target:</b> {name}\n"
        f"<b>Amount:</b> 💵 <code>{amount:,}</code> coins\n\n"
        "<i>Confirm this action?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^admin_coin_"))
async def admin_coin_callback(_, query: types.CallbackQuery):
    if query.from_user.id not in AUTHORIZED_CONSOLES:
        return await query.answer("❌ This is not for you!", show_alert=True)

    data = query.data.split("_")
    action = data[2] # give or take or cancel

    if action == "cancel":
        await query.message.edit_text("❌ <b>Admin action cancelled.</b>", parse_mode=enums.ParseMode.HTML)
        return

    target_id = int(data[3])
    amount = int(data[4])
    
    if action == "give":
        await user_collection.update_one({"id": target_id}, {"$inc": {"balance": amount}}, upsert=True)
        text = f"✅ <b>Successfully added {amount:,} coins!</b>"
    else: # take
        await user_collection.update_one({"id": target_id}, {"$inc": {"balance": -amount}}, upsert=True)
        text = f"✅ <b>Successfully removed {amount:,} coins!</b>"

    # Get new balance
    user = await user_collection.find_one({"id": target_id}, {"balance": 1, "first_name": 1})
    bal = user.get("balance", 0)
    name = user.get("first_name", f"ID: {target_id}")

    await query.message.edit_text(
        f"{text}\n\n"
        f"<b>User:</b> {name}\n"
        f"<b>Final Balance:</b> 💵 <code>{bal:,}</code>",
        parse_mode=enums.ParseMode.HTML
    )
