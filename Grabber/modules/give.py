from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, user_collection

# Define the special admin user who can give/take unlimited balance
UNLIMITED_USER_ID = 7717913705  

async def give_balance(update: Update, context: CallbackContext):
    sender_id = update.effective_user.id

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a user to give balance.")
        return

    recipient_id = update.message.reply_to_message.from_user.id

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid amount. Usage: `/givebalance <amount>` (Reply to user)", parse_mode="Markdown")
        return

    if sender_id == UNLIMITED_USER_ID:
        await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}}, upsert=True)
        await update.message.reply_text(f"✅ {amount} coins given to {update.message.reply_to_message.from_user.username or 'the user'}!")
        return

    sender = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    sender_balance = sender.get("balance", 0) if sender else 0

    if sender_balance < amount:
        await update.message.reply_text("❌ Insufficient balance to give.")
        return

    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}}, upsert=True)
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}}, upsert=True)

    await update.message.reply_text(f"✅ You gave {amount} coins to {update.message.reply_to_message.from_user.username or 'the user'}!")


async def take_balance(update: Update, context: CallbackContext):
    sender_id = update.effective_user.id

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a user to take balance from.")
        return

    recipient_id = update.message.reply_to_message.from_user.id

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid amount. Usage: `/takebalance <amount>` (Reply to user)", parse_mode="Markdown")
        return

    if sender_id == UNLIMITED_USER_ID:
        await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': -amount}})
        await update.message.reply_text(f"✅ {amount} coins taken from {update.message.reply_to_message.from_user.username or 'the user'}!")
        return

    sender = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    sender_balance = sender.get("balance", 0) if sender else 0

    if sender_balance < amount:
        await update.message.reply_text("❌ You don’t have enough coins to take.")
        return

    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': -amount}})
    await update.message.reply_text(f"✅ You took {amount} coins from {update.message.reply_to_message.from_user.username or 'the user'}!")


# Register commands
application.add_handler(CommandHandler("givebalance", give_balance))
application.add_handler(CommandHandler("takebalance", take_balance))
    
