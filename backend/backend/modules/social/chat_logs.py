from pyrogram import filters, types

from backend.client import app
from backend.core.utils import handle_errors
from backend.database import db

group_collection = db['total_groups']

@app.on_message(filters.new_chat_members)
@handle_errors
async def on_new_chat_members(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    new_members = [user.id for user in message.new_chat_members]
    if bot_id in new_members:
        chat_id = message.chat.id
        chat_title = message.chat.title
        existing_group = await group_collection.find_one({"group_id": chat_id})
        if not existing_group:
            await group_collection.insert_one({"group_id": chat_id, "group_name": chat_title})
        # No-op: group DB entry was already written above; nothing to log.
        pass
@app.on_message(filters.left_chat_member)
@handle_errors
async def on_left_chat_member(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    if bot_id == message.left_chat_member.id:
        chat_id = message.chat.id
        await group_collection.delete_one({"group_id": chat_id})
        # No-op: group DB entry was already removed above; nothing to log.
        pass
