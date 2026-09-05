import asyncio
import random

from pyrogram import enums, errors, filters, types

from backend.client import app
from backend.core.balance import check_and_deduct, get_user_balance, update_user_balance
from backend.core.cache import is_on_cooldown as redis_cooldown
from backend.core.logging import get_logger
from backend.core.pokemon import add_pokemon_xp, battle_stats, get_active_pokemon
from backend.core.progression import add_xp
from backend.core.sessions import consume_session, create_session, get_session
from backend.core.utils import handle_errors, html_escape
from backend.modules.progression.achievements import check_achievements
from backend.modules.progression.quests import update_quest_progress

LOGGER = get_logger(__name__)

FALLBACK_STATS = {
    "name": "Fists",
    "types": [],
    "hp": 100,
    "atk": 10,
    "spd": 10,
    "luck": 0.05,
    "level": 1,
    "max_hp": 100,
}

# Standard type-effectiveness chart: attacker type -> {defender type: multiplier}.
# Only non-1x entries listed; everything else is neutral.
TYPE_CHART = {
    "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
    "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
    "ice": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0},
    "ground": {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
    "flying": {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2, "ghost": 2, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
    "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dragon": {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
    "fairy": {"fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5},
}


def type_multiplier(attack_types: list, defend_types: list) -> float:
    """Effectiveness of an attack: product of attacker-type vs defender-type multipliers."""
    mult = 1.0
    for atk_t in attack_types or []:
        row = TYPE_CHART.get(atk_t, {})
        for def_t in defend_types or []:
            mult *= row.get(def_t, 1.0)
    return mult


def effectiveness_text(mult: float) -> str:
    if mult == 0:
        return " 🚫 <b>It had no effect!</b>"
    if mult >= 2:
        return " 🔥 <b>Super effective!</b>"
    if mult < 1:
        return " 💠 <i>Not very effective...</i>"
    return ""


async def calculate_stats(user_id: int) -> dict:
    """
    Combat stats from the user's active Pokémon (level-scaled base stats).
    Falls back to flat Fists stats when no Pokémon is active.
    """
    active = await get_active_pokemon(user_id)
    if not active:
        return dict(FALLBACK_STATS)
    return battle_stats(active)

def simulate_battle(p1_stats, p2_stats, p1_name, p2_name):
    """
    Simulate a turn-based battle between two fighters.
    Determines initiative based on speed and iterates through attacks
    until one fighter's HP reaches zero or the turn limit is hit.
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
        mult = type_multiplier(attacker.get("types"), defender.get("types"))
        damage = int(attacker["atk"] * variance * crit_mult * mult)
        defender["hp"] -= damage
        crit_text = " 💥 <b>CRIT!</b>" if is_crit else ""
        eff_text = effectiveness_text(mult)
        if damage == 0 and mult == 0:
            log.append(f"{a_icon} <b>{a_name}</b>'s attack passed right through {d_name}!")
        else:
            log.append(f"{a_icon} <b>{a_name}</b> hits for <code>{damage}</code>{crit_text}{eff_text} (HP: {max(0, defender['hp'])})")
        if defender["hp"] <= 0:
            break
        attacker, defender = defender, attacker
        a_name, d_name = d_name, a_name
        a_idx, d_idx = d_idx, a_idx
        a_icon, d_icon = d_icon, a_icon
        turn += 1
    winner = a_idx if attacker["hp"] > 0 else d_idx
    if turn > max_turns:
        log.append("\n⚠️ <b>Time Limit Reached!</b> Draw decided by HP.")
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
    if not defender:
        return await message.reply_text("⚠️ Cannot challenge this message (no user attached).", parse_mode=enums.ParseMode.HTML)
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
        return await message.reply_text("❌ You don't have enough Coins!", parse_mode=enums.ParseMode.HTML)
    if await get_user_balance(defender.id) < bet:
        return await message.reply_text(f"❌ <b>{html_escape(defender.first_name)}</b> doesn't have enough Coins!", parse_mode=enums.ParseMode.HTML)
    battle_id = f"bt_{attacker.id}_{defender.id}"
    await create_session(battle_id, {"attacker": attacker.id, "defender": defender.id, "bet": bet})
    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("Accept Challenge", callback_data=f"abt_acc:{battle_id}", style=enums.ButtonStyle.SUCCESS)
    ]])
    await message.reply_to_message.reply_text(
        f"⚔ <a href=\"tg://user?id={attacker.id}\">{html_escape(attacker.first_name)}</a> challenged you to a battle for <b>{bet:,} 🪙</b>!",
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
    battle_info = await consume_session(battle_id)
    if not battle_info:
        return await query.answer("❌ This battle expired or was already handled.", show_alert=True)
    if query.from_user.id != battle_info["defender"]:
        return await query.answer("❌ You are not the challenged person!", show_alert=True)
    bet = battle_info["bet"]
    attacker_id, defender_id = battle_info["attacker"], battle_info["defender"]
    pot_paid = False  # set once the winner has been credited
    if not await check_and_deduct(attacker_id, bet):
        try:
            await query.message.edit_text("❌ Attacker no longer has enough balance.", parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return
    if not await check_and_deduct(defender_id, bet):
        await update_user_balance(attacker_id, bet)
        try:
            await query.message.edit_text("❌ You no longer have enough balance.", parse_mode=enums.ParseMode.HTML)
        except errors.MessageNotModified:
            pass
        return
    try:
        a_user = await app.get_users(attacker_id)
        d_user = await app.get_users(defender_id)
        a_stats = await calculate_stats(attacker_id)
        d_stats = await calculate_stats(defender_id)
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
        pot_paid = True
        await add_xp(winner_id, 30, "battle_win")
        # Pokémon XP: winner's partner gains more, loser's still learns.
        loser_id = defender_id if winner_idx == 1 else attacker_id
        _, winner_evo = await add_pokemon_xp(winner_id, 40, "battle_win")
        _, loser_evo = await add_pokemon_xp(loser_id, 15, "battle_loss")
        loser_user = d_user if winner_idx == 1 else a_user
        evo_lines = []
        for evo, owner in ((winner_evo, winner_user), (loser_evo, loser_user)):
            if evo:
                evo_lines.append(
                    f"✨ <b>{html_escape(evo['from_name'])}</b> evolved into "
                    f"<b>{html_escape(evo['to_name'])}</b> "
                    f"(<a href=\"tg://user?id={owner.id}\">{html_escape(owner.first_name)}</a>)!"
                )
        await update_quest_progress(winner_id, "battle_veteran", 1)
        await update_quest_progress(winner_id, "weekly_battle", 1)
        await update_quest_progress(winner_id, "pass_battles", 1)
        await check_achievements(winner_id)
        result_text = (
            f"📜 <b>Battle Log</b>:\n{battle_log}\n\n"
            f"🏆 <b>Winner:</b> <a href=\"tg://user?id={winner_user.id}\">{html_escape(winner_user.first_name)}</a>\n"
            f"<b>Winnings:</b> <code>{winnings}</code> 🪙\n"
            f"<b>Tax:</b> <code>{tax}</code> 🪙\n"
            f"📈 <b>+30 XP</b> for {html_escape(winner_user.first_name)}"
        )
        if evo_lines:
            result_text += "\n\n" + "\n".join(evo_lines)
        await query.message.edit_text(result_text, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        # Both bets were already deducted. Any failure before the payout
        # (deleted account, Telegram RPCError, DB hiccup) must refund the pot
        # — previously the shards vanished with the exception. If the payout
        # already landed (pot_paid), refunding would double-pay the winner.
        LOGGER.error(f"Battle Error: {e}")
        refund_note = ""
        if not pot_paid:
            try:
                await update_user_balance(attacker_id, bet)
                await update_user_balance(defender_id, bet)
                refund_note = " Both bets were refunded."
            except Exception as refund_err:
                LOGGER.exception(f"CRITICAL: battle refund failed for {attacker_id}/{defender_id}: {refund_err}")
        try:
            await query.message.reply_text(f"❌ A technical error occurred during battle.{refund_note}", parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
