import asyncio
import logging
import random

from pyrogram import enums, filters, types

from backend.client import app
from backend.core.cache import invalidate_user_cache
from backend.core.utils import handle_errors
from backend.database import user_collection

LOGGER = logging.getLogger(__name__)
CURRENCY_SYMBOL = "🪙"
@app.on_message(filters.command("bet"))
@handle_errors
async def bet_cmd(_, message: types.Message):
    user_id = message.from_user.id
    if len(message.command) < 3:
        await message.reply_text(
            "<b>Invalid Usage!</b>\n"
            "Format: <code>/bet &lt;amount&gt; &lt;h/t&gt;</code>\n"
            "Example: <code>/bet 500 h</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    try:
        amount = int(message.command[1])
        choice = message.command[2].lower()
    except ValueError:
        await message.reply_text("Please enter a valid number for the amount.")
        return
    if choice not in ['h', 't']:
        await message.reply_text("Invalid choice! Use <code>h</code> for Heads or <code>t</code> for Tails.", parse_mode=enums.ParseMode.HTML)
        return
    if amount <= 0:
        await message.reply_text("Amount must be a <b>positive number</b>.", parse_mode=enums.ParseMode.HTML)
        return
    user_data = await user_collection.find_one({'id': {'$in': [user_id, str(user_id)]}}, projection={'balance': 1})
    if not user_data:
        await message.reply_text(
            "<b>You don't have an account yet!</b>\n"
            "Use <code>/daily</code> to claim free Coins & start playing!",
            parse_mode=enums.ParseMode.HTML
        )
        return
    balance_amount = user_data.get('balance', 0)
    if balance_amount == 0:
        await message.reply_text(
            "<b>You're out of Coins!</b>\n"
            "Use <code>/daily</code> to claim free Coins & try again!",
            parse_mode=enums.ParseMode.HTML
        )
        return
    # Atomic balance deduction (prevents race conditions)
    update_res = await user_collection.update_one(
        {'id': {'$in': [user_id, str(user_id)]}, 'balance': {'$gte': amount}},
        {'$inc': {'balance': -amount}}
    )

    if update_res.modified_count == 0:
        await message.reply_text(
            f"<b>Not Enough Coins!</b>\n"
            f"Your Balance: <b>{balance_amount:,} 🪙</b>\n\n"
            f"Use <code>/daily</code> to get free Coins!",
            parse_mode=enums.ParseMode.HTML
        )
        return

    user_choice_name = "Heads" if choice == "h" else "Tails"
    await message.reply_text(f"<b>Coin Flip:</b> {amount:,} 🪙\n<b>You Chose:</b> {user_choice_name}", parse_mode=enums.ParseMode.HTML)

    await asyncio.sleep(2)

    # Real coin flip
    coin_result = random.choice(["h", "t"])
    is_win = (choice == coin_result)
    coin_name = "Heads" if coin_result == "h" else "Tails"

    if is_win:
        win_multiplier = 2
        winnings = amount * win_multiplier
        # Credit the winnings; if the DB write fails the stake must go back —
        # otherwise a transient error eats the bet silently.
        try:
            await user_collection.update_one(
                {'id': {'$in': [user_id, str(user_id)]}},
                {'$inc': {'balance': winnings}}
            )
        except Exception:
            LOGGER.exception("BET_CREDIT_FAILED user=%s amount=%s", user_id, winnings)
            try:
                await user_collection.update_one(
                    {'id': {'$in': [user_id, str(user_id)]}},
                    {'$inc': {'balance': amount}}
                )
            except Exception:
                LOGGER.critical("BET_REFUND_FAILED user=%s stake=%s lost", user_id, amount)
            raise

        # Get fresh balance for display
        new_user_data = await user_collection.find_one({'id': {'$in': [user_id, str(user_id)]}}, projection={'balance': 1})
        new_balance = new_user_data.get('balance', 0)

        result_text = (
            f"<b>YOU WIN!</b>\n"
            f"The coin landed on <b>{coin_name}</b>!\n"
            f"<b>You Earned:</b> {winnings:,} 🪙\n\n"
            f"<b>New Balance:</b> {new_balance:,} 🪙"
        )
    else:
        # Balance already deducted
        new_user_data = await user_collection.find_one({'id': {'$in': [user_id, str(user_id)]}}, projection={'balance': 1})
        new_balance = new_user_data.get('balance', 0)

        result_text = (
            f"<b>YOU LOST!</b>\n"
            f"The coin landed on <b>{coin_name}</b>.\n"
            f"<b>You Lost:</b> {amount:,} 🪙\n\n"
            f"<b>New Balance:</b> {new_balance:,} 🪙"
        )

    await invalidate_user_cache(user_id)
    await message.reply_text(result_text, parse_mode=enums.ParseMode.HTML)
