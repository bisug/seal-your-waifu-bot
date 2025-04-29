import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Grabber import application, db, GROUP_ID, BOT_USERNAME, SUPPORT_CHAT, UPDATE_CHAT

# MongoDB Collection
collection = db['total_pm_users']

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = escape(update.effective_user.first_name)  # Escape to prevent HTML issues
    username = update.effective_user.username or "No Username"
    chat_id = update.effective_chat.id

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})

        # Send log message to the group
        log_message = (
            "📌 <b>New User Started the Bot</b>\n\n"
            f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
            f"📛 <b>Username:</b> @{username}\n"
            f"🔗 <b>Profile:</b> <a href='tg://user?id={user_id}'>{first_name}</a>"
        )
        await context.bot.send_message(chat_id=GROUP_ID, text=log_message, parse_mode='HTML')

    # Update user details if changed
    elif user_data['first_name'] != first_name or user_data['username'] != username:
        await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # Private Chat
    if update.effective_chat.type == "private":
        photo_url = "https://files.catbox.moe/2hsawz.jpg"
        caption = """
        ***Heyyyy...***

        ***I am an Open Source Character Catcher Bot! Add me to your group, and I will send random characters every 100 messages. Use /seal to collect characters and check your collection with /harem. Start collecting your harem today!***
        """
        keyboard = [
            [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ Help", callback_data='help')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(chat_id=chat_id, photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')

    # Group Chat
    else:
        photo_url = "https://files.catbox.moe/2hsawz.jpg"
        keyboard = [
            [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(chat_id=chat_id, photo=photo_url, caption="✅ I am active!", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
        ***Help Section:***

        /seal - Guess character (works in groups)  
        /fav - Add to favorites  
        /trade - Trade characters  
        /gift - Gift a character to another user (groups only)  
        /harem - View your collection  
        /topgroups - See top groups  
        /top - View top users  
        /ctop - Your chat’s top rankings  
        /changetime - Change character appearance time (groups only)  
        """
        help_keyboard = [[InlineKeyboardButton("⤾ Back", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await context.bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                               caption=help_text, reply_markup=reply_markup, parse_mode='markdown')

    elif query.data == 'back':
        caption = """
        ***Hey there!*** ✨

        ***I am an Open Source Character Catcher Bot! Add me to your group, and I will send random characters every 100 messages. Use /seal to collect characters and check your collection with /harem. Start collecting your harem today!***
        """
        keyboard = [
            [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("💬 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 Updates", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ Help", callback_data='help')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                               caption=caption, reply_markup=reply_markup, parse_mode='markdown')

# Handlers
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
        
