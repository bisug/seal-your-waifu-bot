from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, OWNER_ID, app, sudo_users, sudo_filter
from Grabber.core.utils import handle_errors
from Grabber.database import sudo_collection
@app.on_message(filters.command("addsudo") & filters.user(OWNER_ID))
@handle_errors
async def addsudo_handler(_, message: types.Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Provide a User ID.", parse_mode=enums.ParseMode.HTML)
    try:
        target_id = int(message.command[1])
        if await sudo_collection.find_one({"user_id": target_id}):
            return await message.reply_text("❗ This user is already a sudo user.", parse_mode=enums.ParseMode.HTML)
        await sudo_collection.insert_one({"user_id": target_id})
        if target_id not in sudo_users:
            sudo_users.append(target_id)
        await message.reply_text(f"✅ User <code>{target_id}</code> added to sudo list.", parse_mode=enums.ParseMode.HTML)
        LOGGER.info(f"New sudo added: {target_id} by {message.from_user.id}")
    except Exception as e:
        LOGGER.error(f"Error adding sudo: {e}")
        await message.reply_text(f"❌ <b>Database Error:</b> Failed to add user.", parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("rmsudo") & filters.user(OWNER_ID))
@handle_errors
async def rmsudo_handler(_, message: types.Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Provide a User ID.", parse_mode=enums.ParseMode.HTML)
    try:
        target_id = int(message.command[1])
        res = await sudo_collection.delete_one({"user_id": target_id})
        if res.deleted_count > 0:
            if target_id in sudo_users:
                sudo_users.remove(target_id)
            await message.reply_text(f"✅ User <code>{target_id}</code> removed from sudo list.", parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text("❌ User not found in sudo list.", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error removing sudo: {e}")
        await message.reply_text(f"❌ <b>Database Error:</b> Failed to remove user.", parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("sudolist") & sudo_filter)
@handle_errors
async def sudolist_handler(_, message: types.Message):
    cursor = sudo_collection.find({})
    sudos = await cursor.to_list(length=None)
    if not sudos:
        return await message.reply_text("Empty sudo list.", parse_mode=enums.ParseMode.HTML)
    text = "👤 <b>Sudo Users List:</b>\n\n"
    for s in sudos:
        user_id = s['user_id']
        try:
            user = await app.get_users(user_id)
            from html import escape
            first_name = escape(user.first_name or "")
            name = f"<a href=\"tg://user?id={user_id}\">{first_name}</a>"
        except Exception:
            name = "<i>Unknown User</i>"
        text += f"• <code>{user_id}</code> — {name}\n"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
