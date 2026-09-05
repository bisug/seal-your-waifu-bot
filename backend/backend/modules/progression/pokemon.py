"""Pokémon bot commands: /mypokemon, /pokedex, /setpokemon."""
from pyrogram import enums, filters, types

from backend.client import app
from backend.core.logging import get_logger
from backend.core.pokemon import (
    ensure_user_pokemon_state,
    find_pokemon,
    get_catalog_pokemon,
    list_catalog_pokemon,
    normalize_pokemon,
    set_active_pokemon,
)
from backend.core.utils import handle_errors, html_escape

LOGGER = get_logger(__name__)

TYPE_EMOJI = {
    "normal": "⭐", "fire": "🔥", "water": "💧", "electric": "⚡", "grass": "🌿",
    "ice": "❄️", "fighting": "🥊", "poison": "☠️", "ground": "⛰️", "flying": "🕊️",
    "psychic": "🔮", "bug": "🐛", "rock": "🪨", "ghost": "👻", "dragon": "🐉",
    "dark": "🌑", "steel": "⚙️", "fairy": "🧚",
}


def type_badges(types: list) -> str:
    return "".join(TYPE_EMOJI.get(t, "❔") for t in types)


@app.on_message(filters.command("mypokemon"))
@handle_errors
async def mypokemon_cmd(_, message: types.Message):
    """List owned Pokémon with the active one highlighted."""
    user_id = message.from_user.id
    user = await ensure_user_pokemon_state(user_id)
    owned = user.get("pokemon", [])
    if not owned:
        return await message.reply_text(
            "🧬 No Pokémon yet! Catch one from a wild spawn in a group chat.",
            parse_mode=enums.ParseMode.HTML,
        )
    current = user.get("current_pokemon")
    catalog = {c["dex"]: c for c in await list_catalog_pokemon(enabled_only=False)}
    lines = ["🧬 <b>Your Pokémon</b>\n"]
    for entry in sorted(owned, key=lambda p: int(p.get("dex", 0))):
        p = normalize_pokemon(entry, catalog.get(int(entry.get("dex", 0))))
        badge = type_badges(p["types"])
        marker = " ⭐" if current is not None and int(entry.get("dex", 0)) == int(current) else ""
        lines.append(
            f"{badge} <b>#{p['dex']:03d} {html_escape(p['name'])}</b> "
            f"Lvl {p['level']} {'/'.join(p['types'])}{marker}"
        )
    lines.append(f"\nTotal: <b>{len(owned)}</b> | Set active: <code>/setpokemon &lt;dex&gt;</code>")
    text = "\n".join(lines)
    # Lead with the active Pokémon's artwork when the list fits a caption.
    img = None
    if current is not None:
        img = (catalog.get(int(current)) or {}).get("img")
    if img and len(text) <= 1024:
        msg = await app.send_media_safe(
            message.chat.id, media_url=img, caption=text, parse_mode=enums.ParseMode.HTML
        )
        if msg:
            return
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("setpokemon"))
@handle_errors
async def setpokemon_cmd(_, message: types.Message):
    """/setpokemon <dex> — make an owned Pokémon active."""
    user_id = message.from_user.id
    try:
        dex = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply_text(
            "❌ Usage: <code>/setpokemon &lt;dex&gt;</code>", parse_mode=enums.ParseMode.HTML
        )
    user = await ensure_user_pokemon_state(user_id)
    if not find_pokemon(user.get("pokemon", []), dex):
        return await message.reply_text(
            "❌ You don't own that Pokémon. See /mypokemon.",
            parse_mode=enums.ParseMode.HTML,
        )
    ok = await set_active_pokemon(user_id, dex)
    cat = await get_catalog_pokemon(dex)
    name = html_escape(cat["name"]) if cat else f"#{dex}"
    if ok:
        text = f"⭐ <b>{name}</b> is now your active Pokémon!"
        img = (cat or {}).get("img")
        if img:
            msg = await app.send_media_safe(
                message.chat.id, media_url=img, caption=text, parse_mode=enums.ParseMode.HTML
            )
            if msg:
                return
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("pokedex"))
@handle_errors
async def pokedex_cmd(_, message: types.Message):
    """/pokedex [name or dex] — look up a Pokémon in the catalog."""
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage: <code>/pokedex &lt;name or dex&gt;</code>", parse_mode=enums.ParseMode.HTML
        )
    raw = message.command[1]
    from backend.database import pokemon_catalog_collection
    if raw.isdigit():
        cat = await pokemon_catalog_collection.find_one({"dex": int(raw)})
    else:
        cat = await pokemon_catalog_collection.find_one(
            {"name": {"$regex": f"^{raw}$", "$options": "i"}}
        )
    if not cat:
        return await message.reply_text("❌ Not found in the Pokédex.", parse_mode=enums.ParseMode.HTML)
    badge = type_badges(cat["types"])
    stats = cat.get("base_stats", {})
    height_m = (cat.get("height_dm") or 0) / 10
    weight_kg = (cat.get("weight_hg") or 0) / 10
    abilities = ", ".join(
        a["name"].replace("-", " ").title() + (" (hidden)" if a.get("is_hidden") else "")
        for a in cat.get("abilities", [])
    ) or "—"
    tags = []
    if cat.get("is_legendary"):
        tags.append("🌟 Legendary")
    if cat.get("is_mythical"):
        tags.append("✨ Mythical")
    gen = (cat.get("generation") or "").replace("generation-", "").upper()
    lines = [
        f"{badge} <b>#{cat['dex']:03d} {html_escape(cat['name'])}</b>",
        f"<b>Type:</b> {'/'.join(cat['types'])}",
        f"<b>Category:</b> {html_escape(cat.get('desc') or 'Pokémon')}",
        f"<b>Height/Weight:</b> {height_m:.1f} m / {weight_kg:.1f} kg",
        f"<b>Abilities:</b> {html_escape(abilities)}",
        f"<b>Base stat total:</b> {cat.get('base_total', '?')}",
        f"<b>Stats:</b> ❤️ {stats.get('hp', '?')} | ⚔️ {stats.get('atk', '?')} | "
        f"🛡 {stats.get('def', '?')} | ✨ {stats.get('spatk', '?')}/{stats.get('spdef', '?')} | 💨 {stats.get('spd', '?')}",
    ]
    if gen:
        lines.append(f"<b>Generation:</b> {gen}")
    if tags:
        lines.append(" ".join(tags))
    if cat.get("flavor_text"):
        lines.append(f"<i>{html_escape(cat['flavor_text'])}</i>")
    caption = "\n".join(lines)
    # Inline buttons for the full stats / moves breakdowns.
    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton(
                "🔖 Stats", callback_data=f"pdex_stats_{cat['dex']}"
            ),
            types.InlineKeyboardButton(
                "⚔️ Moves", callback_data=f"pdex_moves_{cat['dex']}"
            ),
        ]
    ])
    img = cat.get("img") or cat.get("shiny_img")
    if img:
        try:
            return await app.send_media_safe(
                message.chat.id,
                media_url=img,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=markup,
            )
        except Exception as e:
            LOGGER.warning(f"Pokédex photo failed, falling back to text: {e}")
    await message.reply_text(caption, parse_mode=enums.ParseMode.HTML, reply_markup=markup)


def _pdex_stats_text(cat: dict) -> str:
    stats = cat.get("base_stats", {})
    rows = [
        ("❤️ HP", stats.get("hp")),
        ("⚔️ Attack", stats.get("atk")),
        ("🛡 Defense", stats.get("def")),
        ("✨ Sp. Atk", stats.get("spatk")),
        ("✨ Sp. Def", stats.get("spdef")),
        ("💨 Speed", stats.get("spd")),
    ]
    lines = [f"{badge} <b>#{cat['dex']:03d} {html_escape(cat['name'])} — Base Stats</b>\n"]
    for label, value in rows:
        lines.append(f"• <b>{label}:</b> {value if value is not None else '?'}")
    lines.append(f"\n<b>Total:</b> {cat.get('base_total', '?')}")
    return "\n".join(lines)


def _pdex_moves_text(cat: dict) -> str:
    moves = cat.get("moves", [])
    if not moves:
        return f"{html_escape(cat['name'])} has no moves recorded."
    pretty = ", ".join(m.replace("-", " ").title() for m in moves)
    return f"{badge_of(cat)} <b>#{cat['dex']:03d} {html_escape(cat['name'])} — Moves ({len(moves)})</b>\n\n{html_escape(pretty)}"


def badge_of(cat: dict) -> str:
    return type_badges(cat.get("types", []))


@app.on_callback_query(filters.regex(r"^pdex_(stats|moves)_(\d+)$"))
@handle_errors
async def pdex_callback(_, query: types.CallbackQuery):
    """Show the stats or moves breakdown for the Pokédex entry."""
    parts = query.data.split("_")
    action, dex = parts[1], int(parts[2])
    cat = await get_catalog_pokemon(dex)
    if not cat:
        return await query.answer("Pokémon not found.", show_alert=True)
    if action == "stats":
        text = _pdex_stats_text(cat)
    else:
        text = _pdex_moves_text(cat)
    # Telegram captions cap at 1024 chars; long move lists go as a new message.
    if len(text) > 1000:
        text = text[:997] + "…"
    await query.answer()
    await query.message.reply_text(text, parse_mode=enums.ParseMode.HTML)
