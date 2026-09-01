from pyrogram import enums, filters, types

from backend import sudo_filter
from backend.client import app
from backend.core.roles import sudo_users
from backend.core.user import add_user_set_on_insert
from backend.core.utils import handle_errors, html_escape
from backend.database import user_collection
from config import config


async def get_target_user(message: types.Message):
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
            try:
                user = await app.get_users(target_id)
                name = user.first_name
            except Exception:
                name = f"ID: {target_id}"
            return target_id, amount, name
        except (IndexError, ValueError):
            return None, None, None
@app.on_message(filters.command("givecoin") & sudo_filter)
@handle_errors
async def give_coin_handler(_, message: types.Message):
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
        f"<b>Action:</b> GIVING Shards\n"
        f"<b>Target:</b> {html_escape(name)}\n"
        f"<b>Amount:</b> {amount:,} ⬪\n\n"
        f"<i>Confirm this action?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
@app.on_message(filters.command("takecoin") & sudo_filter)
@handle_errors
async def take_coin_handler(_, message: types.Message):
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
        f"<b>Action:</b> TAKING Shards\n"
        f"<b>Target:</b> {html_escape(name)}\n"
        f"<b>Amount:</b> {amount:,} ⬪\n\n"
        f"<i>Confirm this action?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^admin_coin_"))
async def admin_coin_callback(_, query: types.CallbackQuery):
    if query.from_user.id not in sudo_users and query.from_user.id != config.OWNER_ID:
        return await query.answer("❌ This is not for you!", show_alert=True)
    data = query.data.split("_")
    action = data[2]
    if action == "cancel":
        await query.message.edit_text("❌ <b>Admin action cancelled.</b>", parse_mode=enums.ParseMode.HTML)
        return
    target_id = int(data[3])
    amount = int(data[4])
    if action == "give":
        await user_collection.update_one(
            {"id": target_id},
            add_user_set_on_insert({"$inc": {"balance": amount}}, target_id),
            upsert=True
        )
        text = f"✅ <b>Successfully added {amount:,} ⬪!</b>"
    else:
        await user_collection.update_one(
            {"id": target_id},
            add_user_set_on_insert({"$inc": {"balance": -amount}}, target_id),
            upsert=True
        )
        text = f"✅ <b>Successfully removed {amount:,} ⬪!</b>"
    user = await user_collection.find_one({"id": target_id}, {"balance": 1, "first_name": 1})
    bal = user.get("balance", 0)
    name = user.get("first_name", f"ID: {target_id}")
    await query.message.edit_text(
        f"{text}\n\n"
        f"<b>User:</b> {html_escape(name)}\n"
        f"<b>Final Balance:</b> {bal:,} ⬪",
        parse_mode=enums.ParseMode.HTML
    )
