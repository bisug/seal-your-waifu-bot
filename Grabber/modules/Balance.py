import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient

from Grabber import user_collection, collection, application

SUPPORT_GROUP_ID = -1002429397912  
OWNER_ID = 6574393060  
current_characters = {}  

MAX_ACTIVE_GAMES = 100  

async def add_coins(user_id: int, amount: int):
    if amount <= 0:
        return
    user_data = await user_collection.find_one({"id": user_id}, projection={"balance": 1})
    if user_data:
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
    else:
        await user_collection.insert_one({"id": user_id, "balance": amount})

async def balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    balance_amount = user_data.get('balance', 0) if user_data else 0
    await update.message.reply_text(f"Your balance: 💵 {balance_amount} coins.")

async def pay(update: Update, context: CallbackContext):
    sender_id = update.effective_user.id
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to use /pay.")
        return

    recipient_id = update.message.reply_to_message.from_user.id
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Usage: /pay <amount>")
        return

    sender_balance = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    if not sender_balance or sender_balance.get('balance', 0) < amount:
        await update.message.reply_text("Insufficient balance.")
        return

    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})

    updated_sender_balance = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    await update.message.reply_text(
        f"💵 Payment successful! You paid {amount} coins to {update.message.reply_to_message.from_user.username}. "
        f"Your balance: 💵 {updated_sender_balance.get('balance', 0)} coins."
    )

async def daily_reward(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_daily_reward': 1, 'balance': 1})

    if user_data:
        last_claimed_date = user_data.get('last_daily_reward')
        if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
            await update.message.reply_text("You've already claimed your daily reward today.")
            return

    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 150}, '$set': {'last_daily_reward': datetime.utcnow()}}
    )
    await update.message.reply_text("🎉 You've claimed your daily reward of 150 coins!")

async def mtop(update: Update, context: CallbackContext):
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'balance': 1}).sort('balance', -1).limit(10).to_list(10)

    top_message = "🏆 **Top 10 Users with Highest Balance:**\n"
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        user_id = user.get('id', 'Unknown')
        top_message += f"{i}. <a href='tg://user?id={user_id}'>{first_name}</a> - 💵 {user.get('balance', 0)} coins\n"

    await update.message.reply_photo(
        photo='https://telegra.ph/file/8fce79d744297133b79b6.jpg',
        caption=top_message,
        parse_mode='HTML'
    )

async def nguess(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if chat_id != SUPPORT_GROUP_ID:
        await update.message.reply_text("❌ This command only works in @TNJBotSupport .")
        return

    if len(current_characters) >= MAX_ACTIVE_GAMES:
        await update.message.reply_text("⚠️ Too many active waifu games! Wait for others to finish.")
        return

    characters = await collection.aggregate([{"$sample": {"size": 1}}]).to_list(1)
    if not characters:
        await update.message.reply_text("No waifus found in the database.")
        return

    character = characters[0]
    character_name = character['name'].strip().lower()

    current_characters[chat_id] = {
        "character": character,
        "guessed": False
    }

    await update.message.reply_photo(photo=character['img_url'], caption="✨ Guess this Waifu! 🧐✨")

    
async def handle_guess(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return  

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    guess = update.message.text.strip().lower()

    if chat_id not in current_characters:
        return

    data = current_characters[chat_id]
    character = data["character"]
    character_name = character['name'].strip().lower()

    if not data["guessed"]:
        correct_words = set(character_name.split())
        guess_words = set(guess.split())

        valid_guesses = [word for word in guess_words if len(word) > 1]  

        if correct_words.intersection(valid_guesses):  
            await add_coins(user_id, 100)
            await update.message.reply_text(f"🎉 Correct! You earned 100 coins!")

            del current_characters[chat_id]
            await nguess(update, context)
           
            


async def name(update: Update, context: CallbackContext):
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        chat_id = update.effective_chat.id
        if chat_id in current_characters:
            character_name = current_characters[chat_id]["character"]["name"]
            copy_text = f"`{character_name}`"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📋 Copy Name", switch_inline_query=copy_text)]])

            await update.message.reply_text(f"📜 Character Name: `{character_name}`", reply_markup=keyboard, parse_mode="Markdown")
        else:
            return  
    else:
        return  
        
WEEKLY_INTERVAL = 7  # Users can claim a weekly bonus every 7 days

# 🎁 /bonus - One-time claim only
async def bonus(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'bonus_claimed': 1, 'balance': 1})

    if user_data and user_data.get('bonus_claimed'):
        await update.message.reply_text("❌ You have **already claimed** this bonus! No more bonus available.")
        return

    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 3000}, '$set': {'bonus_claimed': True}},
        upsert=True
    )
    await update.message.reply_text("🎁 You've claimed your **one-time bonus** of **3000 coins**! 💰")


# 🎉 /weekly - Claim every 7 days
async def weekly_bonus(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_weekly_bonus': 1, 'balance': 1})

    if user_data:
        last_claimed_date = user_data.get('last_weekly_bonus')
        if last_claimed_date and (datetime.utcnow() - last_claimed_date).days < WEEKLY_INTERVAL:
            await update.message.reply_text("❌ You've already claimed your weekly bonus. Come back later!")
            return

    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 750}, '$set': {'last_weekly_bonus': datetime.utcnow()}},
        upsert=True
    )
    await update.message.reply_text("🎉 You've claimed your **weekly bonus** of **750 coins**! 💰")

application.add_handler(CommandHandler("bonus", bonus))
application.add_handler(CommandHandler("weekly", weekly_bonus))    
application.add_handler(CommandHandler(["balance", "bal"], balance))
application.add_handler(CommandHandler("pay", pay))
application.add_handler(CommandHandler("daily", daily_reward))
application.add_handler(CommandHandler("mtop", mtop))
application.add_handler(CommandHandler("nguess", nguess))
application.add_handler(CommandHandler("name", name))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    
