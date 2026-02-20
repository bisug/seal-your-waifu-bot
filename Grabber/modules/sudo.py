from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.app import app
from Grabber import OWNER_ID, sudo_users, LOGGER
from Grabber.database import sudo_collection

@app.on_message(filters.command("addsudo") & filters.user(OWNER_ID))
async def addsudo_handler(_, message: types.Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Provide a User ID.", parse_mode=ParseMode.MARKDOWN_V2)

    target_id = int(message.command[1])
    if await sudo_collection.find_one({"user_id": target_id}):
        return await message.reply_text("❗ This user is already a sudo user.", parse_mode=ParseMode.MARKDOWN_V2)

    await sudo_collection.insert_one({"user_id": target_id})
    if target_id not in sudo_users:
        sudo_users.append(target_id)
        
    await message.reply_text(f"✅ User `{target_id}` added to sudo list.", parse_mode=ParseMode.MARKDOWN_V2)
    LOGGER.info(f"New sudo added: {target_id} by {message.from_user.id}")

@app.on_message(filters.command("rmsudo") & filters.user(OWNER_ID))
async def rmsudo_handler(_, message: types.Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Provide a User ID.", parse_mode=ParseMode.MARKDOWN_V2)

    target_id = int(message.command[1])
    res = await sudo_collection.delete_one({"user_id": target_id})
    
    if res.deleted_count > 0:
        if target_id in sudo_users:
            sudo_users.remove(target_id)
        await message.reply_text(f"✅ User `{target_id}` removed from sudo list.", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await message.reply_text("❌ User not found in sudo list.", parse_mode=ParseMode.MARKDOWN_V2)

@app.on_message(filters.command("sudolist") & filters.user([OWNER_ID] + sudo_users))
async def sudolist_handler(_, message: types.Message):
    cursor = sudo_collection.find({})
    sudos = await cursor.to_list(length=None)
    
    if not sudos:
        return await message.reply_text("Empty sudo list.", parse_mode=ParseMode.MARKDOWN_V2)
        
    text = "👤 **Sudo Users List:**\n\n"
    for s in sudos:
        text += f"• `{s['user_id']}`\n"
        
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
