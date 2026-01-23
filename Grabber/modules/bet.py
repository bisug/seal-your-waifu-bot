import asyncio
import random
from pyrogram import filters, types, enums
from Grabber import app, user_collection

CURRENCY_SYMBOL = "⨭"  # Unique currency symbol

@app.on_message(filters.command("bet"))
async def bet_cmd(_, message: types.Message):
    """Handles the /bet command for coin flipping."""
    user_id = message.from_user.id
    
    if len(message.command) < 3:
        await message.reply_text(
            f"🚨 **Invalid Usage!**\n"
            f"🎲 Format: `/bet <amount> <h/t>`\n"
            f"🎭 Example: `/bet 500 h`",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    try:
        amount = int(message.command[1])  # Bet amount
        choice = message.command[2].lower()  # "h" for heads, "t" for tails
    except ValueError:
        await message.reply_text("❌ Please enter a valid number for the amount.")
        return

    if choice not in ['h', 't']:
        await message.reply_text("❌ Invalid choice! Use `h` for Heads or `t` for Tails.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    if amount <= 0:
        await message.reply_text("❌ Amount must be a **positive number**.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    # Fetch user balance
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if not user_data:
        await message.reply_text(
            f"💰 **You don't have an account yet!**\n"
            f"🔥 Use `/bonus` to claim free {CURRENCY_SYMBOL} & start betting!",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    balance_amount = user_data.get('balance', 0)

    if balance_amount == 0:
        await message.reply_text(
            f"💰 **You're out of {CURRENCY_SYMBOL}!**\n"
            f"🔥 Use `/bonus` to claim free {CURRENCY_SYMBOL} & try again!",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    if balance_amount < amount:
        await message.reply_text(
            f"❌ **Not Enough {CURRENCY_SYMBOL}!**\n"
            f"🏦 Your Balance: **{CURRENCY_SYMBOL} {balance_amount}**\n\n"
            f"🔥 Use `/bonus` to get free {CURRENCY_SYMBOL}!",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    user_choice_name = "Heads" if choice == "h" else "Tails"
    await message.reply_text(f"🎰 **Placing Bet:** {CURRENCY_SYMBOL} {amount}\n🪙 **You Chose:** {user_choice_name}", parse_mode=enums.ParseMode.MARKDOWN)  

    await asyncio.sleep(2)  # Suspense delay

    # 40% win chance as per original logic
    is_win = random.randint(1, 100) <= 40

    if is_win:
        win_multiplier = 2 # 2x as per original winning = amount * 2
        winnings = amount * win_multiplier
        new_balance = balance_amount + winnings  
        result_text = (
            f"🎉 **YOU WIN!** 🎉\n"
            f"🪙 The coin landed on **{user_choice_name}**!\n"
            f"💰 **You Earned:** {CURRENCY_SYMBOL} {winnings}\n\n"
            f"🏦 **New Balance:** {CURRENCY_SYMBOL} {new_balance}"
        )
    else:
        new_balance = balance_amount - amount  
        comp_choice = "Heads" if user_choice_name == "Tails" else "Tails"
        result_text = (
            f"💔 **YOU LOST!**\n"
            f"🪙 The coin landed on **{comp_choice}**.\n"
            f"💸 **You Lost:** {CURRENCY_SYMBOL} {amount}\n\n"
            f"🏦 **New Balance:** {CURRENCY_SYMBOL} {new_balance}"
        )

    # Update user balance
    await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})

    await message.reply_text(result_text, parse_mode=enums.ParseMode.MARKDOWN)
