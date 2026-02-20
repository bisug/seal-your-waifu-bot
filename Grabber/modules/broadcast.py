import asyncio
from pyrogram import filters, types, enums, errors
from pyrogram.enums import ParseMode
from Grabber import app
from Grabber import OWNER_ID, LOGGER
from Grabber.database import total_pm_users, group_collection

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ **Reply to a message to broadcast.**")

    cmd_parts = message.text.split()
    send_users = "-u" in cmd_parts
    send_groups = "-g" in cmd_parts
    
                                 
    if not send_users and not send_groups:
        send_users = send_groups = True

    msg = message.reply_to_message
    status = await message.reply_text("🚀 **Broadcast started...**")
    
    success_u = failed_u = success_g = failed_g = 0

    if send_users:
        async for user in total_pm_users.find({}, {"_id": 1}):
            user_id = user["_id"]
            try:
                await msg.forward(user_id)
                success_u += 1
                await asyncio.sleep(0.05)                                     
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.forward(user_id)
                success_u += 1
            except (errors.UserIsBlocked, errors.PeerIdInvalid):
                failed_u += 1
                await total_pm_users.delete_one({"_id": user_id})
            except Exception as e:
                failed_u += 1
                LOGGER.error(f"Broadcast User Error ({user_id}): {e}")

    if send_groups:
        async for group in group_collection.find({}, {"group_id": 1}):
            group_id = group["group_id"]
            try:
                await msg.forward(group_id)
                success_g += 1
                await asyncio.sleep(0.05)
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.forward(group_id)
                success_g += 1
            except (errors.ChatWriteForbidden, errors.ChatAdminRequired):
                failed_g += 1
            except Exception as e:
                failed_g += 1
                LOGGER.error(f"Broadcast Group Error ({group_id}): {e}")

    summary = (
        "📊 **Broadcast Complete**\n\n"
        f"👤 **Users:** `{success_u}` successful / `{failed_u}` failed\n"
        f"👥 **Groups:** `{success_g}` successful / `{failed_g}` failed"
    )
    await status.edit_text(summary, parse_mode=ParseMode.MARKDOWN_V2)
