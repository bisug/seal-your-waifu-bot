from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import (
    Grabberu as app, 
    JOINLOGS, LEAVELOGS, db, LOGGER
)

group_collection = db['total_groups']

                                   
async def send_log(chat_id: str, message: str):
    try:
        await app.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error sending log message: {e}")

                                    
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    new_members = [user.id for user in message.new_chat_members]

    if bot_id in new_members:
        chat_id = message.chat.id
        chat_title = message.chat.title
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"
        added_by = f"<a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>" if message.from_user else "Unknown User"

                                                       
        existing_group = await group_collection.find_one({"group_id": chat_id})
        if not existing_group:
            await group_collection.insert_one({"group_id": chat_id, "group_name": chat_title})

                         
        log_text = (
            f"✫ #NEW_GROUP ✫\n"
            f"✫ <b>Group:</b> {html_escape(chat_title)}\n"
            f"✫ <b>Group ID:</b> <code>{chat_id}</code>\n"
            f"✫ <b>Username:</b> {html_escape(chat_username)}\n"
            f"✫ <b>Added By:</b> {added_by}"
        )
        await send_log(JOINLOGS, log_text)

                                                       
@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    if bot_id == message.left_chat_member.id:
        chat_id = message.chat.id
        chat_title = message.chat.title
        remove_by = f"<a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>" if message.from_user else "Unknown User"
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"

                                        
        await group_collection.delete_one({"group_id": chat_id})

                         
        log_text = (
            f"✫ #LEFT_GROUP ✫\n"
            f"✫ <b>Group:</b> {html_escape(chat_title)}\n"
            f"✫ <b>Group ID:</b> <code>{chat_id}</code>\n"
            f"✫ <b>Username:</b> {html_escape(chat_username)}\n"
            f"✫ <b>Removed By:</b> {remove_by}"
        )
        await send_log(LEAVELOGS, log_text)
