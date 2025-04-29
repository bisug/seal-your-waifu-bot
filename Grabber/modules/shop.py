import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, user_collection

async def give_coin(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != 7717913705:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid amount! Use: `/givecoin <amount>`")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({"id": user_id})

    if not user_data:
        await update.message.reply_text("❌ You are not registered!")
        return

    new_balance = user_data.get("balance", 0) + amount
    await user_collection.update_one({"id": user_id}, {"$set": {"balance": new_balance}})

    await update.message.reply_text(f"✅ {amount} coins added!\n💰 New Balance: {new_balance} coins.")

application.add_handler(CommandHandler('givecoin', give_coin, block=False))
