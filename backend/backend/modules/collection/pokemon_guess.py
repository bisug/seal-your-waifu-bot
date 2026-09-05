"""Guess-the-Pokémon: chat minigame where users type the spawn's name.

A wild Pokémon spawns as a spoilered artwork; the first correct name in
chat claims it. Rewards: coins + user XP + active-partner XP (which can
trigger evolution — announced in the win message).
"""
import re

from pyrogram import enums, filters, types

from backend.client import app
from backend.core.balance import update_user_balance
from backend.core.logging import get_logger
from backend.core.pokemon import add_pokemon_xp
from backend.core.progression import add_xp
from backend.core.spawns import (
    POKEMON_GUESS_MON_XP,
    POKEMON_GUESS_REWARD,
    POKEMON_GUESS_XP,
    clear_active_pokemon_spawn,
    get_active_pokemon_spawn,
)
from backend.core.tasks import run_background_task
from backend.core.utils import handle_errors, html_escape

LOGGER = get_logger(__name__)


def _name_variants(name: str) -> set[str]:
    """Matchable lowercase variants: full name plus long parts.

    Mirrors the nguess heuristic: 'pikachu' or 'raichu' style single names
    match exactly; multi-word names (e.g. 'Mr Mime') also match any single
    part longer than 2 chars.
    """
    name = name.lower().strip()
    parts = re.split(r"\s+", name)
    variants = {name}
    for part in parts:
        if len(part) > 2:
            variants.add(part)
    return variants


@app.on_message(filters.group & filters.text & ~filters.bot & ~filters.command(["seal", "nguess", "top", "ctop"]), group=2)
@handle_errors
async def pokemon_guess_handler(_, message: types.Message):
    """First correct Pokémon name in chat claims the spawn + rewards."""
    if not message.from_user or not message.text:
        return
    chat_id = message.chat.id
    spawn = await get_active_pokemon_spawn(chat_id)
    if not spawn:
        return
    guess = message.text.lower().strip()
    if guess not in _name_variants(spawn["name"]):
        return
    user = message.from_user
    if not await clear_active_pokemon_spawn(chat_id, user.id):
        return  # someone else claimed it first
    # Rewards — none block the win message.
    _, evo = await add_pokemon_xp(user.id, POKEMON_GUESS_MON_XP, "pokemon_guess")
    run_background_task(update_user_balance(user.id, POKEMON_GUESS_REWARD))
    run_background_task(add_xp(user.id, POKEMON_GUESS_XP, "pokemon_guess"))
    mention = f'<a href="tg://user?id={user.id}">{html_escape(user.first_name)}</a>'
    text = (
        f"✅ {mention} guessed the Pokémon!\n"
        f"🌀 It was <b>{html_escape(spawn['name'])}</b> (#{spawn['dex']:03d})\n"
        f"💰 <b>Reward:</b> +{POKEMON_GUESS_REWARD} Coins\n"
        f"📈 <b>+{POKEMON_GUESS_XP} XP</b> · partner <b>+{POKEMON_GUESS_MON_XP} XP</b>"
    )
    if evo:
        text += (
            f"\n✨ <b>{html_escape(evo['from_name'])}</b> evolved into "
            f"<b>{html_escape(evo['to_name'])}</b>!"
        )
    try:
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Failed to send Pokémon guess result: {e}")
