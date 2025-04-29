import asyncio
import random
from telegram.ext import CommandHandler
from Grabber import application, user_collection
from telegram import Update
from telegram.ext import ContextTypes

CURRENCY_SYMBOL = "⨭"  # Unique currency symbol

async def bet(update: Update, context: ContextTypes):
    """Handles the /bet command for coin flipping."""
    user_id = update.effective_user.id
    
    try:
        amount = int(context.args[0])  # Bet amount
        choice = context.args[1].lower()  # "h" for heads, "t" for tails
    except (IndexError, ValueError):
        await update.message.reply_text(
            f"🚨 **Invalid Usage!**\n"
            f"🎲 Format: `/bet <amount> <h/t>`\n"
            f"🎭 Example: `/bet 500 h`",
            parse_mode='Markdown'
        )
        return

    if choice not in ['h', 't']:
        await update.message.reply_text("❌ Invalid choice! Use `h` for Heads or `t` for Tails.", parse_mode='Markdown')
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be a **positive number**.", parse_mode='Markdown')
        return

    # Fetch user balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if not user_data:
        await update.message.reply_text(
            f"💰 **You don't have an account yet!**\n"
            f"🔥 Use `/bonus` to claim free {CURRENCY_SYMBOL} & start betting!",
            parse_mode="Markdown"
        )
        return

    balance_amount = user_data.get('balance', 0)

    if balance_amount == 0:
        await update.message.reply_text(
            f"💰 **You're out of {CURRENCY_SYMBOL}!**\n"
            f"🔥 Use `/bonus` to claim free {CURRENCY_SYMBOL} & try again!",
            parse_mode="Markdown"
        )
        return

    if balance_amount < amount:
        await update.message.reply_text(
            f"❌ **Not Enough {CURRENCY_SYMBOL}!**\n"
            f"🏦 Your Balance: **{CURRENCY_SYMBOL} {balance_amount}**\n\n"
            f"🔥 Use `/bonus` to get free {CURRENCY_SYMBOL}!",
            parse_mode="Markdown"
        )
        return

    user_choice = "Heads" if choice == "h" else "Tails"
    await update.message.reply_text(f"🎰 **Placing Bet:** {CURRENCY_SYMBOL} {amount}\n🪙 **You Chose:** {user_choice}")  

    await asyncio.sleep(2)  # Suspense delay

    is_win = random.randint(1, 100) <= 40  # 40% win chance

    if is_win:
        winnings = amount * 2  # 3x WIN
        new_balance = balance_amount + winnings  
        result_text = f"🎉 **YOU WIN!** 🎉\n🪙 The coin landed on **{user_choice}**!\n💰 **You Earned:** {CURRENCY_SYMBOL} {winnings}\n\n🏦 **New Balance:** {CURRENCY_SYMBOL} {new_balance}"
    else:
        new_balance = balance_amount - amount  
        result_text = f"💔 **YOU LOST!**\n🪙 The coin landed on **{'Heads' if user_choice == 'Tails' else 'Tails'}**.\n💸 **You Lost:** {CURRENCY_SYMBOL} {amount}\n\n🏦 **New Balance:** {CURRENCY_SYMBOL} {new_balance}"

    # Update user balance
    await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})

    await update.message.reply_text(result_text, parse_mode="Markdown")

# Adding command handler
application.add_handler(CommandHandler("bet", bet, block=False))
