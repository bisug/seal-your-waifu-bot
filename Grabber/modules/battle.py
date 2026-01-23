import asyncio
import random
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import LOGGER
from Grabber.core.game import get_user_balance, update_user_balance, check_and_deduct

active_battles = {}

@app.on_message(filters.command("battle") & filters.group)
async def battle_challenge_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Challenge someone by replying to their message!")

    attacker = message.from_user
    defender = message.reply_to_message.from_user

    if attacker.id == defender.id:
        return await message.reply_text("⚠️ You can't fight yourself!")

    try:
        bet = int(message.command[1])
        if bet <= 0: raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("❌ Usage: `/battle <bet_amount>`")

    # Fast balance check
    if await get_user_balance(attacker.id) < bet:
        return await message.reply_text("❌ You don't have enough coins!")
    
    if await get_user_balance(defender.id) < bet:
        return await message.reply_text(f"❌ {defender.first_name} doesn't have enough coins!")

    battle_id = f"{attacker.id}_{defender.id}"
    active_battles[battle_id] = {"attacker": attacker.id, "defender": defender.id, "bet": bet}

    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("⚔ Accept", callback_data=f"abt_acc:{battle_id}")
    ]])

    await message.reply_to_message.reply_text(
        f"⚔ {attacker.mention} challenged you to a battle for **{bet}** coins!",
        reply_markup=markup,
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_callback_query(filters.regex(r"^abt_acc:"))
async def battle_accept_handler(_, query: types.CallbackQuery):
    battle_id = query.data.split(":")[1]
    battle_info = active_battles.get(battle_id)

    if not battle_info:
        return await query.answer("❌ This battle expired.", show_alert=True)

    if query.from_user.id != battle_info["defender"]:
        return await query.answer("❌ You are not the challenged person!", show_alert=True)

    bet = battle_info["bet"]
    attacker_id, defender_id = battle_info["attacker"], battle_info["defender"]

    # Atomic deduction
    if not await check_and_deduct(attacker_id, bet):
        return await query.message.edit_text("❌ Attacker no longer has enough balance.")
    
    if not await check_and_deduct(defender_id, bet):
        # Refund attacker
        await update_user_balance(attacker_id, bet)
        return await query.message.edit_text("❌ You no longer have enough balance.")

    active_battles.pop(battle_id, None)
    
    try:
        a_user = await app.get_users(attacker_id)
        d_user = await app.get_users(defender_id)

        await query.message.edit_text(f"⚔️ **Battle Started!**\n{a_user.mention} 🆚 {d_user.mention}\n\n🔥 **Fighting...**")
        await app.send_chat_action(query.message.chat.id, enums.ChatAction.TYPING)
        
        await asyncio.sleep(2)
        
        # Battle flavor text logic separated or simplified
        winner_id = random.choice([attacker_id, defender_id])
        winnings = bet * 2 # Total pot is bet*2

        await update_user_balance(winner_id, winnings)
        winner_user = a_user if winner_id == attacker_id else d_user

        await query.message.reply_text(
            f"🏆 **Winner:** {winner_user.mention}\n💰 **Winnings:** {winnings} coins!",
            parse_mode=enums.ParseMode.MARKDOWN
        )

    except Exception as e:
        LOGGER.error(f"Battle Error: {e}")
        # In a real app, you might want to refund both if it crashes here
        await query.message.reply_text("❌ A technical error occurred during battle.")
