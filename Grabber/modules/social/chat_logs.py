from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, app, db
from Grabber.core.utils import handle_errors, html_escape

group_collection = db['total_groups']
async def send_log(chat_id: str, message: str):
    pass
@app.on_message(filters.new_chat_members)
@handle_errors
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
        # Database entry for new group handled here, no log sent.
        pass
@app.on_message(filters.left_chat_member)
@handle_errors
async def on_left_chat_member(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    if bot_id == message.left_chat_member.id:
        chat_id = message.chat.id
        chat_title = message.chat.title
        remove_by = f"<a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>" if message.from_user else "Unknown User"
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"
        await group_collection.delete_one({"group_id": chat_id})
        # Database entry removal handled here, no log sent.
        pass
