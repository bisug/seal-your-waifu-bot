import asyncio
import random
import time
from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, app
from Grabber.core.balance import (check_and_deduct, get_user_balance,
                                  update_user_balance)
from Grabber.core.cache import is_on_cooldown as redis_cooldown
from Grabber.core.progression import add_xp
from Grabber.core.sessions import create_session, delete_session, get_session
from Grabber.core.user import get_active_pet
from Grabber.core.utils import handle_errors, html_escape
from Grabber.modules.progression.achievements import check_achievements
from Grabber.modules.progression.quests import update_quest_progress
def calculate_stats(pet_data):
    """
    Calculate derived combat stats from pet base stats and level.
    Provides default stats if no pet is active.
    """
    if not pet_data:
        return {
            "name": "Fists",
            "hp": 100,
            "atk": 10,
            "spd": 10,
            "luck": 0.05,
            "level": 1
        }
    level = pet_data.get("level", 1)
    base_hp = pet_data.get("hp", 150)
    base_atk = pet_data.get("atk", 20)
    base_spd = pet_data.get("spd", 15)
    return {
        "name": pet_data["name"],
        "hp": base_hp + (level * 5),
        "atk": base_atk + (level * 2),
        "spd": base_spd + (level * 1),
        "luck": pet_data.get("luck", 0.1),
        "level": level,
        "max_hp": base_hp + (level * 5)
    }
def simulate_battle(p1_stats, p2_stats, p1_name, p2_name):
    """
    Simulate a turn-based battle between two pets.
    Determines initiative based on speed and iterates through attacks
    until one pet's HP reaches zero or the turn limit is hit.
    """
    log = []
    if p1_stats["spd"] >= p2_stats["spd"]:
        attacker, defender = p1_stats, p2_stats
        a_name, d_name = p1_name, p2_name
        a_idx, d_idx = 1, 2
        a_icon, d_icon = "🔴", "🔵"
    else:
        attacker, defender = p2_stats, p1_stats
        a_name, d_name = p2_name, p1_name
        a_idx, d_idx = 2, 1
        a_icon, d_icon = "🔵", "🔴"
    turn = 1
    max_turns = 15
    log.append(f"⏱️ <b>Initiative:</b> {a_icon} <b>{a_name}</b> ({attacker['spd']} SPD) goes first!")
    while attacker["hp"] > 0 and defender["hp"] > 0 and turn <= max_turns:
        crit_mult = 1.0
        is_crit = False
        if random.random() < attacker["luck"]:
            crit_mult = 1.5
            is_crit = True
        variance = random.uniform(0.9, 1.1)
        damage = int(attacker["atk"] * variance * crit_mult)
        defender["hp"] -= damage
        crit_text = " 💥 <b>CRIT!</b>" if is_crit else ""
        hp_bar = "▓" * int((max(0, defender['hp']) / defender['max_hp']) * 5)
        log.append(f"{a_icon} <b>{a_name}</b> hits for <code>{damage}</code>{crit_text} (HP: {max(0, defender['hp'])})")
        if defender["hp"] <= 0:
            break
        attacker, defender = defender, attacker
        a_name, d_name = d_name, a_name
        a_idx, d_idx = d_idx, a_idx
        a_icon, d_icon = d_icon, a_icon
        turn += 1
    winner = a_idx if attacker["hp"] > 0 else d_idx
    if turn > max_turns:
        log.append(f"\n⚠️ <b>Time Limit Reached!</b> Draw decided by HP.")
        if p1_stats["hp"] > p2_stats["hp"]:
            winner = 1
        else:
            winner = 2
    return winner, "\n".join(log)
@app.on_message(filters.command("battle") & filters.group)
@handle_errors
async def battle_challenge_handler(_, message: types.Message):
    """
    Handle the /battle command to challenge another user.
    Validates the bet and creates a temporary session for the challenge.
    """
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Challenge someone by replying to their message!", parse_mode=enums.ParseMode.HTML)
    attacker = message.from_user
    defender = message.reply_to_message.from_user
    if attacker.id == defender.id:
        return await message.reply_text("⚠️ You can't fight yourself!", parse_mode=enums.ParseMode.HTML)
    # Redis-based cooldown (survives restarts)
    pair_key = f"battle_{min(attacker.id, defender.id)}_{max(attacker.id, defender.id)}"
    on_cd, remain = await redis_cooldown(pair_key, 0, 300)
    if on_cd:
        return await message.reply_text(f"⏳ <b>Cooldown!</b> Wait {remain}s before battling this user again.", parse_mode=enums.ParseMode.HTML)
    try:
        bet = int(message.command[1])
        if bet <= 0: raise ValueError
    except (IndexError, ValueError):
        return await message.reply_text("❌ Usage: <code>/battle &lt;bet_amount&gt;</code>", parse_mode=enums.ParseMode.HTML)
    if await get_user_balance(attacker.id) < bet:
        return await message.reply_text("❌ You don't have enough Shards!", parse_mode=enums.ParseMode.HTML)
    if await get_user_balance(defender.id) < bet:
        return await message.reply_text(f"❌ <b>{html_escape(defender.first_name)}</b> doesn't have enough Shards!", parse_mode=enums.ParseMode.HTML)
    battle_id = f"bt_{attacker.id}_{defender.id}"
    await create_session(battle_id, {"attacker": attacker.id, "defender": defender.id, "bet": bet})
    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("Accept Challenge", callback_data=f"abt_acc:{battle_id}", style=enums.ButtonStyle.SUCCESS)
    ]])
    await message.reply_to_message.reply_text(
        f"⚔ <a href=\"tg://user?id={attacker.id}\">{html_escape(attacker.first_name)}</a> challenged you to a battle for <b>{bet:,} ⬪</b>!",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^abt_acc:"))
async def battle_accept_handler(_, query: types.CallbackQuery):
    """
    Handle the callback when a user accepts a battle challenge.
    Deducts shards, performs the simulation, and awards the winner.
    """
    battle_id = query.data.split(":")[1]
    battle_info = await get_session(battle_id)
    if not battle_info:
        return await query.answer("❌ This battle expired or was already handled.", show_alert=True)
    if query.from_user.id != battle_info["defender"]:
        return await query.answer("❌ You are not the challenged person!", show_alert=True)
    bet = battle_info["bet"]
    attacker_id, defender_id = battle_info["attacker"], battle_info["defender"]
    if not await check_and_deduct(attacker_id, bet):
        await delete_session(battle_id)
        try:
            await query.message.edit_text("❌ Attacker no longer has enough balance.", parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return
    if not await check_and_deduct(defender_id, bet):
        await update_user_balance(attacker_id, bet)
        await delete_session(battle_id)
        try:
            await query.message.edit_text("❌ You no longer have enough balance.", parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return
    await delete_session(battle_id)
    try:
        a_user = await app.get_users(attacker_id)
        d_user = await app.get_users(defender_id)
        a_pet_data = await get_active_pet(attacker_id)
        d_pet_data = await get_active_pet(defender_id)
        a_stats = calculate_stats(a_pet_data)
        d_stats = calculate_stats(d_pet_data)
        text = (
            f"⚔️ <b>Battle Started!</b>\n"
            f"🔴 <a href=\"tg://user?id={a_user.id}\">{html_escape(a_user.first_name)}</a> - <b>{html_escape(a_stats['name'])}</b> (Lvl {a_stats['level']})\n"
            f"   ❤️ {a_stats['hp']} | ⚔️ {a_stats['atk']} | ⚡ {a_stats['spd']}\n"
            f" 🆚 \n"
            f"🔵 <a href=\"tg://user?id={d_user.id}\">{html_escape(d_user.first_name)}</a> - <b>{html_escape(d_stats['name'])}</b> (Lvl {d_stats['level']})\n"
            f"   ❤️ {d_stats['hp']} | ⚔️ {d_stats['atk']} | ⚡ {d_stats['spd']}\n\n"
            f"🔥 <b>Fighting...</b>"
        )
        try:
            await query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        await asyncio.sleep(2)
        winner_idx, battle_log = simulate_battle(a_stats.copy(), d_stats.copy(), a_stats['name'], d_stats['name'])
        winner_id = attacker_id if winner_idx == 1 else defender_id
        winner_user = a_user if winner_idx == 1 else d_user
        total_pot = bet * 2
        tax = int(total_pot * 0.10)
        winnings = total_pot - tax
        await update_user_balance(winner_id, winnings)
        await add_xp(winner_id, 30, "battle_win")
        await update_quest_progress(winner_id, "battle_veteran", 1)
        await update_quest_progress(winner_id, "weekly_battle", 1)
        await check_achievements(winner_id)
        result_text = (
            f"📜 <b>Battle Log</b>:\n{battle_log}\n\n"
            f"🏆 <b>Winner:</b> <a href=\"tg://user?id={winner_user.id}\">{html_escape(winner_user.first_name)}</a>\n"
            f"<b>Winnings:</b> <code>{winnings}</code> ⬪\n"
            f"<b>Tax:</b> <code>{tax}</code> ⬪\n"
            f"📈 <b>+30 XP</b> for {html_escape(winner_user.first_name)}"
        )
        await query.message.edit_text(result_text, parse_mode=enums.ParseMode.HTML)

    except errors.RPCError as e:
        LOGGER.error(f"Battle Error: {e}")
        try:
            await query.message.reply_text("❌ A technical error occurred during battle.", parse_mode=enums.ParseMode.HTML)
        except:
            pass
