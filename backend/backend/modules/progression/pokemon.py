"""Pokémon bot commands: /mypokemon, /pokedex, /starter, /setpokemon."""
from pyrogram import enums, filters, types

from backend.client import app
from backend.core.logging import get_logger
from backend.core.pokemon import (
    STARTER_DEXES,
    ensure_user_pokemon_state,
    find_pokemon,
    get_catalog_pokemon,
    grant_pokemon,
    list_catalog_pokemon,
    normalize_pokemon,
    set_active_pokemon,
)
from backend.core.utils import get_user_id_query, handle_errors, html_escape
from backend.database import user_collection

LOGGER = get_logger(__name__)

TYPE_EMOJI = {
    "normal": "⭐", "fire": "🔥", "water": "💧", "electric": "⚡", "grass": "🌿",
    "ice": "❄️", "fighting": "🥊", "poison": "☠️", "ground": "⛰️", "flying": "🕊️",
    "psychic": "🔮", "bug": "🐛", "rock": "🪨", "ghost": "👻", "dragon": "🐉",
    "dark": "🌑", "steel": "⚙️", "fairy": "🧚",
}


def type_badges(types: list) -> str:
    return "".join(TYPE_EMOJI.get(t, "❔") for t in types)


@app.on_message(filters.command("starter"))
@handle_errors
async def starter_cmd(_, message: types.Message):
    """One-time starter Pokémon selection for existing users."""
    user_id = message.from_user.id
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user:
        return await message.reply_text("Start the bot first with /start.", parse_mode=enums.ParseMode.HTML)
    if user.get("starter_claimed"):
        return await message.reply_text(
            "✅ You already claimed your starter Pokémon!", parse_mode=enums.ParseMode.HTML
        )
    starters = []
    for dex in STARTER_DEXES:
        cat = await get_catalog_pokemon(dex)
        if cat:
            starters.append(cat)
    if not starters:
        return await message.reply_text(
            "⚠️ Pokémon catalog is empty. Ask an admin to run the import.",
            parse_mode=enums.ParseMode.HTML,
        )
    lines = ["🧬 <b>Choose your starter Pokémon!</b>\n"]
    for i, cat in enumerate(starters, 1):
        badge = type_badges(cat["types"])
        lines.append(f"<b>{i}.</b> {badge} <b>{html_escape(cat['name'])}</b> — {'/'.join(cat['types'])}")
    lines.append("\nReply with <code>/starter &lt;number&gt;</code> to choose.")
    await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("starter") & filters.regex(r"^/starter\s+\d+\s*$"))
@handle_errors
async def starter_pick_handler(_, message: types.Message):
    """Catch the numbered pick (runs after the menu handler above)."""
    user_id = message.from_user.id
    try:
        pick = int(message.command[1]) - 1
    except (IndexError, ValueError):
        return
    if not 0 <= pick < len(STARTER_DEXES):
        return await message.reply_text("❌ Invalid choice.", parse_mode=enums.ParseMode.HTML)
    user = await user_collection.find_one(get_user_id_query(user_id))
    if not user or user.get("starter_claimed"):
        return
    dex = STARTER_DEXES[pick]
    # Atomic claim: only the first writer of starter_claimed wins.
    res = await user_collection.update_one(
        {**get_user_id_query(user_id), "starter_claimed": {"$ne": True}},
        {"$set": {"starter_claimed": True}},
    )
    if res.modified_count == 0:
        return await message.reply_text(
            "✅ You already claimed your starter Pokémon!", parse_mode=enums.ParseMode.HTML
        )
    granted = await grant_pokemon(user_id, dex, level=5)
    if not granted:
        return await message.reply_text("❌ Starter unavailable.", parse_mode=enums.ParseMode.HTML)
    await set_active_pokemon(user_id, dex)
    cat = await get_catalog_pokemon(dex)
    name = html_escape(cat["name"]) if cat else f"#{dex}"
    await message.reply_text(
        f"🎉 <b>{name}</b> joined your team and is now your active Pokémon!",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("mypokemon"))
@handle_errors
async def mypokemon_cmd(_, message: types.Message):
    """List owned Pokémon with the active one highlighted."""
    user_id = message.from_user.id
    user = await ensure_user_pokemon_state(user_id)
    owned = user.get("pokemon", [])
    if not owned:
        return await message.reply_text(
            "🧬 No Pokémon yet! Claim a starter with /starter.",
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
    await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)


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
        await message.reply_text(
            f"⭐ <b>{name}</b> is now your active Pokémon!", parse_mode=enums.ParseMode.HTML
        )


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
    await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)
