import asyncio
from pyrogram import Client, filters
from pymongo import MongoClient
from Grabber import Grabberu as app  

# MongoDB Connection
mongo_url = "REDACTED_MONGO_URI"
client = MongoClient(mongo_url)
db = client['Character_catchers']

# Collections
user_collection = db['total_pm_users']  
group_collection = db['total_groups']

OWNER_ID = 6574393060  # Change this to your Telegram ID

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ **Reply to a message to broadcast.**")
        return

    args = message.text.split()
    send_to_users = "-user" in args
    send_to_groups = "-group" in args

    # If no option is provided, send to both users and groups
    if not send_to_users and not send_to_groups:
        send_to_users = send_to_groups = True

    broadcast_msg = message.reply_to_message
    sent_users = failed_users = sent_groups = failed_groups = 0

    # **Broadcast to Users**
    if send_to_users:
        users = list(user_collection.find({}, {"user_id": 1}))  # Convert cursor to list
        for user in users:
            user_id = user["user_id"]
            try:
                await broadcast_msg.forward(user_id)
                sent_users += 1
            except Exception as e:
                failed_users += 1
                print(f"❌ Failed to send to user {user_id}: {e}")

    # **Broadcast to Groups**
    if send_to_groups:
        group_ids = group_collection.distinct("group_id")  # No need to await
        for group_id in group_ids:
            try:
                await broadcast_msg.forward(group_id)
                sent_groups += 1
            except Exception as e:
                failed_groups += 1
                print(f"❌ Failed to send to group {group_id}: {e}")

    # **Send Broadcast Summary**
    await message.reply_text(
        f"📊 **Broadcast Summary:**\n\n"
        f"👤 **Total Users:** `{user_collection.count_documents({})}`\n"
        f"👥 **Total Groups:** `{len(group_collection.distinct('group_id'))}`\n\n"
        f"✅ **Sent to Users:** `{sent_users}`\n"
        f"❌ **Failed Users:** `{failed_users}`\n"
        f"✅ **Sent to Groups:** `{sent_groups}`\n"
        f"❌ **Failed Groups:** `{failed_groups}`"
    )
    
