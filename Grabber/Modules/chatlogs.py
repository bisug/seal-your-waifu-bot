import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from Grabber import user_collection, group_collection, Grabberu as app  

# **Logging Groups**
JOINLOGS = "@seal_Your_WH_Group"
LEAVELOGS = "@seal_Your_WH_Group"

# **MongoDB Connection** (Already connected in `Grabber`)
mongo_url = "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client['Character_catchers']
group_collection = db['total_groups']

# **Function to Send Log Messages**
async def send_log(chat_id: str, message: str):
    try:
        await app.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Error sending log message: {e}")

# **Auto-Add New Group to Database**
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    new_members = [user.id for user in message.new_chat_members]

    if bot_id in new_members:
        chat_id = message.chat.id
        chat_title = message.chat.title
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"
        added_by = message.from_user.mention if message.from_user else "Unknown User"

        # **Check if group already exists in database**
        existing_group = group_collection.find_one({"group_id": chat_id})
        if not existing_group:
            group_collection.insert_one({"group_id": chat_id, "group_name": chat_title})

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
async def on_left_chat_member(client, message):
    bot_id = (await client.get_me()).id
    if bot_id == message.left_chat_member.id:
        chat_id = message.chat.id
        chat_title = message.chat.title
        remove_by = message.from_user.mention if message.from_user else "Unknown User"
        chat_username = f"@{message.chat.username}" if message.chat.username else "Private Chat"

        # **Remove Group from Database**
        group_collection.delete_one({"group_id": chat_id})

        # **Log Message**
        log_text = (
            f"✫ #LEFT_GROUP ✫\n"
            f"✫ **Group:** {chat_title}\n"
            f"✫ **Group ID:** `{chat_id}`\n"
            f"✫ **Username:** {chat_username}\n"
            f"✫ **Removed By:** {remove_by}"
        )
        await send_log(LEAVELOGS, log_text)
        
