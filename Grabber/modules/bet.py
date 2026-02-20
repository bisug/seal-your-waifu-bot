import asyncio
import random
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, user_collection

CURRENCY_SYMBOL = "⬪"                 

@app.on_message(filters.command("bet"))
async def bet_cmd(_, message: types.Message):
                                                     
    user_id = message.from_user.id
    
    if len(message.command) < 3:
        await message.reply_text(
            f"🚨 **Invalid Usage!**\n"
            f"🎲 Format: `/bet <amount> <h/t>`\n"
            f"🎭 Example: `/bet 500 h`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        amount = int(message.command[1])              
        choice = message.command[2].lower()                                
    except ValueError:
        await message.reply_text("❌ Please enter a valid number for the amount.")
        return

    if choice not in ['h', 't']:
        await message.reply_text("❌ Invalid choice! Use `h` for Heads or `t` for Tails.", parse_mode=ParseMode.MARKDOWN)
        return

    if amount <= 0:
        await message.reply_text("❌ Amount must be a **positive number**.", parse_mode=ParseMode.MARKDOWN)
        return

                        
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if not user_data:
        await message.reply_text(
            f"💰 **You don't have an account yet!**\n"
            f"🔥 Use `/bonus` to claim free Shards & start betting!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    balance_amount = user_data.get('balance', 0)

    if balance_amount == 0:
        await message.reply_text(
            f"💰 **You're out of Shards!**\n"
            f"🔥 Use `/bonus` to claim free Shards & try again!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if balance_amount < amount:
        await message.reply_text(
            f"❌ **Not Enough Shards!**\n"
            f"🏦 Your Balance: **{balance_amount:,} ⬪**\n\n"
            f"🔥 Use `/bonus` to get free Shards!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    user_choice_name = "Heads" if choice == "h" else "Tails"
    await message.reply_text(f"🎰 **Placing Bet:** {amount:,} ⬪\n🪙 **You Chose:** {user_choice_name}", parse_mode=ParseMode.MARKDOWN)  

    await asyncio.sleep(2)                  

                                          
    is_win = random.randint(1, 100) <= 40

    if is_win:
        win_multiplier = 2                                          
        winnings = amount * win_multiplier
        new_balance = balance_amount + winnings  
        result_text = (
            f"🎉 **YOU WIN!** 🎉\n"
            f"🪙 The coin landed on **{user_choice_name}**!\n"
            f"💰 **You Earned:** {winnings:,} ⬪\n\n"
            f"🏦 **New Balance:** {new_balance:,} ⬪"
        )
    else:
        new_balance = balance_amount - amount  
        comp_choice = "Heads" if user_choice_name == "Tails" else "Tails"
        result_text = (
            f"💔 **YOU LOST!**\n"
            f"🪙 The coin landed on **{comp_choice}**.\n"
            f"💸 **You Lost:** {amount:,} ⬪\n\n"
            f"🏦 **New Balance:** {new_balance:,} ⬪"
        )

                         
    await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})

    await message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
