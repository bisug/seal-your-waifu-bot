import os
import html
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import (
    application, user_collection, top_global_groups_collection, 
    group_user_totals_collection
)

OWNER_ID = 7717913705
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    if not leaderboard_data:
        await update.message.reply_text("No groups found in the leaderboard yet.")
        return

    leaderboard_message = "<b>🏆 Top 10 Grabber Groups</b>\n\n"

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))
        count = group.get('count', 0)
        
        if len(group_name) > 15:  
            group_name = group_name[:15] + '...'  

        leaderboard_message += f"{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n"

    await update.message.reply_text(leaderboard_message, parse_mode='HTML')

async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title or 'This Group'

    cursor = user_collection.aggregate([
        {"$match": {"groups": {"$in": [chat_id]}}},  
        {"$project": {"user_id": 1, "first_name": 1, "waifu_count": 1}},  
        {"$sort": {"waifu_count": -1}},  
        {"$limit": 10}  
    ])
    leaderboard_data = await cursor.to_list(length=10)

    if not leaderboard_data:
        await update.message.reply_text(f"No users found in the leaderboard for {html.escape(chat_name)}.")
        return

    leaderboard_message = f"<b>🏆 Top 10 Grabbers in {html.escape(chat_name)}</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        user_id = user.get('user_id')
        first_name = user.get('first_name', '').strip() or f"User {user_id}"
        waifu_count = user.get('waifu_count', 0)

        if len(first_name) > 15:
            first_name = first_name[:15] + '...'

        leaderboard_message += f"{i}. <a href='tg://user?id={user_id}'>{first_name}</a> ➾ <b>{waifu_count}</b>\n"

    await update.message.reply_text(leaderboard_message, parse_mode='HTML')
    
async def leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "username": 1, "first_name": 1, "characters": 1})
    leaderboard_data = await cursor.to_list(length=None)

    leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)
    leaderboard_data = leaderboard_data[:10]

    leaderboard_message = "<b>🏆 Top 10 Users with Most Characters</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        user_id = user.get('id')
        username = user.get('username')
        first_name = user.get('first_name', '').strip()

        # Agar database me first_name missing hai toh API se fetch karo
        if not first_name:
            try:
                chat = await context.bot.get_chat(user_id)  # Telegram API Call
                first_name = chat.first_name or f"User {user_id}"
            except:
                first_name = f"User {user_id}"

        display_name = f"@{username}" if username else html.escape(first_name)

        if len(display_name) > 15:
            display_name = display_name[:15] + '...'

        leaderboard_message += f"{i}. <a href='tg://user?id={user_id}'>{display_name}</a> ➾ <b>{len(user.get('characters', []))}</b>\n"

    await update.message.reply_text(leaderboard_message, parse_mode='HTML')
    
async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = await user_collection.count_documents({})
    group_count = len(await group_user_totals_collection.distinct('group_id'))

    await update.message.reply_text(f'Total Users: {user_count}\nTotal Groups: {group_count}')

async def send_users_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text('Only for Sudo users...')
        return

    cursor = user_collection.find({})
    users = [document async for document in cursor]
    user_list = "\n".join(user.get('first_name', 'Unknown') for user in users)

    with open('users.txt', 'w') as f:
        f.write(user_list)

    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('users.txt')

async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text('Only for Sudo users...')
        return

    cursor = top_global_groups_collection.find({})
    groups = [document async for document in cursor]
    group_list = "\n\n".join(group.get('group_name', 'Unknown') for group in groups)

    with open('groups.txt', 'w') as f:
        f.write(group_list)

    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    os.remove('groups.txt')

# ✅ Fixed Application Handler Registration
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))
    
