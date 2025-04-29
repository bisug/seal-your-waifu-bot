from pyrogram import Client, filters
from pymongo import MongoClient
from Grabber import Grabberu as app  

# MongoDB Connection
mongo_url = "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client['Character_catchers']

# Collections
user_collection = db['total_pm_users']  
group_collection = db['total_groups']

ADMIN_ID = 7717913705  

# 📢 **Custom Broadcast Command**
@app.on_message(filters.command("broadcasts") & filters.user(ADMIN_ID))
async def broadcast_message(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a message to broadcast.")
        return

    broadcast_message = message.reply_to_message  # **Replied Message**
    args = message.text.split()  # Get Command Arguments  
    target_users = "-user" in args
    target_groups = "-group" in args
    pin_message = "-pin" in args  

    if not target_users and not target_groups:
        target_users, target_groups = True, True  # Default: Send to All

    sent_count, failed_count = 0, 0

    # 🚀 **Forward to Users (if -user)**
    if target_users:
        users = user_collection.find({}, {"id": 1})  
        for user in users:
            try:
                user_id = user.get("id")
                if user_id:
                    await client.forward_messages(user_id, message.chat.id, broadcast_message.id)  
                    sent_count += 1
            except Exception as e:
                print(f"❌ Failed to send to user {user_id}: {e}")
                failed_count += 1  

    # 🚀 **Forward to Groups (if -group or -pin)**
    if target_groups or pin_message:
        groups = group_collection.find({}, {"group_id": 1})  
        for group in groups:
            try:
                group_id = group.get("group_id")
                if group_id:
                    msg = await client.forward_messages(group_id, message.chat.id, broadcast_message.id)  
                    if pin_message:
                        await client.pin_chat_message(group_id, msg.id, disable_notification=True)  
                    sent_count += 1
            except Exception as e:
                print(f"❌ Failed to send to group {group_id}: {e}")
                failed_count += 1  

    # ✅ **Summary Report**
    await message.reply_text(f"📢 **Broadcast Completed!**\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}")
@app.on_message(filters.command("y"))
async def send_stats(client, message):
    user_count = user_collection.count_documents({})
    group_count = group_collection.count_documents({})

    await message.reply_text(
        f"📊 **Bot Stats:**\n"
        f"👤 **Total Users:** `{user_count}`\n"
        f"👥 **Total Groups:** `{group_count}`"
    )
