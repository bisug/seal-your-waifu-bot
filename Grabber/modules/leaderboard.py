import html
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import user_collection, top_global_groups_collection, group_user_totals_collection

@app.on_message(filters.command("top"))
async def global_leaderboard_handler(_, message: types.Message):
    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
    # Logic: Aggregation for top users
    cursor = user_collection.aggregate([
        {"$project": {"first_name": 1, "id": 1, "char_count": {"$size": {"$ifNull": ["$characters", []]}}}},
        {"$sort": {"char_count": -1}},
        {"$limit": 10}
    ])
    
    top_users = await cursor.to_list(length=10)
    
    text = "🏆 **Global Top 10 Grabbers**\n\n"
    for i, user in enumerate(top_users, 1):
        name = html.escape(user.get('first_name', 'User'))
        text += f"{i}. {name} ➾ **{user['char_count']}**\n"
        
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("ctop") & filters.group)
async def chat_leaderboard_handler(_, message: types.Message):
    chat_id = message.chat.id
    
    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    
    top_members = await cursor.to_list(length=10)
    
    text = f"🏆 **Top Members in {message.chat.title}**\n\n"
    for i, member in enumerate(top_members, 1):
        user_id = member['user_id']
        try:
            m = await app.get_users(user_id)
            name = m.first_name
        except Exception:
            name = f"User {user_id}"
        
        text += f"{i}. {name} ➾ **{member['count']}**\n"
        
    await message.reply_text(text)
