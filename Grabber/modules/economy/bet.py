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
            f"🚨 <b>Invalid Usage!</b>\n"
            f"🎲 Format: <code>/bet &lt;amount&gt; &lt;h/t&gt;</code>\n"
            f"🎭 Example: <code>/bet 500 h</code>",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        amount = int(message.command[1])
        choice = message.command[2].lower()
    except ValueError:
        await message.reply_text("❌ Please enter a valid number for the amount.")
        return

    if choice not in ['h', 't']:
        await message.reply_text("❌ Invalid choice! Use <code>h</code> for Heads or <code>t</code> for Tails.", parse_mode=ParseMode.HTML)
        return

    if amount <= 0:
        await message.reply_text("❌ Amount must be a <b>positive number</b>.", parse_mode=ParseMode.HTML)
        return


    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if not user_data:
        await message.reply_text(
            f"💰 <b>You don't have an account yet!</b>\n"
            f"🔥 Use <code>/bonus</code> to claim free Shards &amp; start betting!",
            parse_mode=ParseMode.HTML
        )
        return

    balance_amount = user_data.get('balance', 0)

    if balance_amount == 0:
        await message.reply_text(
            f"💰 <b>You're out of Shards!</b>\n"
            f"🔥 Use <code>/bonus</code> to claim free Shards &amp; try again!",
            parse_mode=ParseMode.HTML
        )
        return

    if balance_amount < amount:
        await message.reply_text(
            f"❌ <b>Not Enough Shards!</b>\n"
            f"🏦 Your Balance: <b>{balance_amount:,} ⬪</b>\n\n"
            f"🔥 Use <code>/bonus</code> to get free Shards!",
            parse_mode=ParseMode.HTML
        )
        return

    user_choice_name = "Heads" if choice == "h" else "Tails"
    await message.reply_text(f"🎰 <b>Placing Bet:</b> {amount:,} ⬪\n🪙 <b>You Chose:</b> {user_choice_name}", parse_mode=ParseMode.HTML)

    await asyncio.sleep(2)


    is_win = random.randint(1, 100) <= 40

    if is_win:
        win_multiplier = 2
        winnings = amount * win_multiplier
        new_balance = balance_amount + winnings
        result_text = (
            f"🎉 <b>YOU WIN!</b> 🎉\n"
            f"🪙 The coin landed on <b>{user_choice_name}</b>!\n"
            f"💰 <b>You Earned:</b> {winnings:,} ⬪\n\n"
            f"🏦 <b>New Balance:</b> {new_balance:,} ⬪"
        )
    else:
        new_balance = balance_amount - amount
        comp_choice = "Heads" if user_choice_name == "Tails" else "Tails"
        result_text = (
            f"💔 <b>YOU LOST!</b>\n"
            f"🪙 The coin landed on <b>{comp_choice}</b>.\n"
            f"💸 <b>You Lost:</b> {amount:,} ⬪\n\n"
            f"🏦 <b>New Balance:</b> {new_balance:,} ⬪"
        )


    await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}})

    await message.reply_text(result_text, parse_mode=ParseMode.HTML)
