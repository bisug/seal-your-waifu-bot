import asyncio
import random
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import LOGGER
from Grabber.core.game import get_user_balance, update_user_balance, check_and_deduct
from Grabber.core.sessions import create_session, get_session, delete_session
from Grabber.core.user import get_active_pet

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
        return await message.reply_text("❌ Usage: <code>/battle &lt;bet_amount&gt;</code>", parse_mode=enums.ParseMode.HTML)

    # Fast balance check
    if await get_user_balance(attacker.id) < bet:
        return await message.reply_text("❌ You don't have enough coins!")
    
    if await get_user_balance(defender.id) < bet:
        return await message.reply_text(f"❌ {defender.first_name} doesn't have enough coins!")

    # Store challenge in MongoDB
    battle_id = f"bt_{attacker.id}_{defender.id}"
    await create_session(battle_id, {"attacker": attacker.id, "defender": defender.id, "bet": bet})

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
    battle_info = await get_session(battle_id)

    if not battle_info:
        return await query.answer("❌ This battle expired or was already handled.", show_alert=True)

    if query.from_user.id != battle_info["defender"]:
        return await query.answer("❌ You are not the challenged person!", show_alert=True)

    bet = battle_info["bet"]
    attacker_id, defender_id = battle_info["attacker"], battle_info["defender"]

    # Atomic deduction
    if not await check_and_deduct(attacker_id, bet):
        await delete_session(battle_id)
        return await query.message.edit_text("❌ Attacker no longer has enough balance.")
    
    if not await check_and_deduct(defender_id, bet):
        await update_user_balance(attacker_id, bet)
        await delete_session(battle_id)
        return await query.message.edit_text("❌ You no longer have enough balance.")

    await delete_session(battle_id)
    
    try:
        a_user = await app.get_users(attacker_id)
        d_user = await app.get_users(defender_id)
        
        # Fetch Pets
        a_pet = await get_active_pet(attacker_id)
        d_pet = await get_active_pet(defender_id)
        
        a_luck = a_pet["luck"] if a_pet else 0.0
        d_luck = d_pet["luck"] if d_pet else 0.0
        
        a_pet_name = a_pet["name"] if a_pet else "Hand-to-Hand"
        d_pet_name = d_pet["name"] if d_pet else "Hand-to-Hand"

        text = (
            f"⚔️ **Battle Started!**\n"
            f"👤 {a_user.mention} (w/ {a_pet_name})\n"
            f" 🆚 \n"
            f"👤 {d_user.mention} (w/ {d_pet_name})\n\n"
            f"🔥 **Fighting...**"
        )
        await query.message.edit_text(text, parse_mode=enums.ParseMode.MARKDOWN)
        await app.send_chat_action(query.message.chat.id, enums.ChatAction.TYPING)
        
        await asyncio.sleep(2)
        
        # Win logic: Base 50% + luck difference (capped at 20% shift)
        luck_diff = (a_luck - d_luck) * 100
        luck_diff = max(-20, min(20, luck_diff))
        a_win_chance = 50 + luck_diff
        
        roll = random.uniform(0, 100)
        winner_id = attacker_id if roll <= a_win_chance else defender_id
        winnings = bet * 2

        await update_user_balance(winner_id, winnings)
        winner_user = a_user if winner_id == attacker_id else d_user
        winner_pet = a_pet_name if winner_id == attacker_id else d_pet_name

        result_text = (
            f"🏆 **Winner:** {winner_user.mention}\n"
            f"🐾 **MVP:** {winner_pet}\n"
            f"💰 **Winnings:** {winnings} coins!\n"
            f"📈 **Odds:** {int(a_win_chance)}% vs {int(100 - a_win_chance)}%"
        )

        await query.message.reply_text(result_text, parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        LOGGER.error(f"Battle Error: {e}")
        await query.message.reply_text("❌ A technical error occurred during battle.")
