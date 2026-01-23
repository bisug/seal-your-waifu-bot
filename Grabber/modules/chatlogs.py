from pyrogram import filters, types, enums
from Grabber import (
    Grabberu as app, 
    JOINLOGS, LEAVELOGS, db, LOGGER
)

group_collection = db['total_groups']

# **Function to Send Log Messages**
async def send_log(chat_id: str, message: str):
    try:
        await app.send_message(chat_id=chat_id, text=message, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        LOGGER.error(f"Error sending log message: {e}")

# **Auto-Add New Group to Database**
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    new_members = [user.id for user in message.new_chat_members]

    if bot_id in new_members:
        chat_id = message.chat.id
        chat_title = message.chat.title
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"
        added_by = message.from_user.mention if message.from_user else "Unknown User"

        # **Check if group already exists in database**
        existing_group = await group_collection.find_one({"group_id": chat_id})
        if not existing_group:
            await group_collection.insert_one({"group_id": chat_id, "group_name": chat_title})

        # **Log Message**
        log_text = (
            f"✫ #NEW_GROUP ✫\n"
            f"✫ **Group:** {chat_title}\n"
            f"✫ **Group ID:** `{chat_id}`\n"
            f"✫ **Username:** {chat_username}\n"
            f"✫ **Added By:** {added_by}"
        )
        await send_log(JOINLOGS, log_text)

# **Auto-Remove Group from Database if Bot is Removed**
@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: types.Message):
    me = await app.get_me()
    bot_id = me.id
    if bot_id == message.left_chat_member.id:
        chat_id = message.chat.id
        chat_title = message.chat.title
        remove_by = message.from_user.mention if message.from_user else "Unknown User"
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"

        # **Remove Group from Database**
        await group_collection.delete_one({"group_id": chat_id})

        # **Log Message**
        log_text = (
            f"✫ #LEFT_GROUP ✫\n"
            f"✫ **Group:** {chat_title}\n"
            f"✫ **Group ID:** `{chat_id}`\n"
            f"✫ **Username:** {chat_username}\n"
            f"✫ **Removed By:** {remove_by}"
        )
        await send_log(LEAVELOGS, log_text)
