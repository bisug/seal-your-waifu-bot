from pyrogram import enums, filters, types

from backend import app, sudo_filter
from backend.core.rarities import (
    EDITABLE_FIELDS,
    RARITY_MAP,
    bare_name,
    get_rarity_docs,
    refresh_rarities,
    set_rarity_field,
    add_rarity,
)
from backend.core.utils import handle_errors, html_escape


def _resolve_rarity(token: str) -> str | None:
    """Resolve a rarity by number, full label, or bare name."""
    token = token.strip()
    if token.isdigit() and int(token) in RARITY_MAP:
        return RARITY_MAP[int(token)]
    for label in RARITY_MAP.values():
        if token == label or token.lower() == bare_name(label).lower():
            return label
    return None


@app.on_message(filters.command("rarityconfig") & sudo_filter)
@handle_errors
async def rarity_config_handler(_, message: types.Message):
    lines = [
        "<b>Rarity Config (DB-backed)</b>",
        "<i>num · label · spawn/active/shop/claim weights · price ⧫ · stock · sell ⬪</i>",
        "",
    ]
    for doc in get_rarity_docs():
        lines.append(
            f"<code>{doc.get('num')}</code> {html_escape(doc['_id'])} — "
            f"w:{doc.get('spawn_weight')}/{doc.get('active_spawn_weight')}/"
            f"{doc.get('shop_weight')}/{doc.get('claim_weight')} · "
            f"{doc.get('shop_price')}⧫ · stock {doc.get('stock_limit')} · "
            f"sell {doc.get('sell_price')}⬪"
        )
    lines.extend([
        "",
        "<b>Edit:</b> <code>/rarityset &lt;num|name&gt; &lt;field&gt; &lt;value&gt;</code>",
        f"<b>Fields:</b> {', '.join(sorted(EDITABLE_FIELDS))}",
        "<b>Add:</b> <code>/rarityadd &lt;num&gt; &lt;emoji Label&gt;</code>",
        "<b>Reload:</b> <code>/rarityrefresh</code>",
    ])
    await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("rarityset") & sudo_filter)
@handle_errors
async def rarity_set_handler(_, message: types.Message):
    if len(message.command) < 4:
        return await message.reply_text(
            "<b>Usage:</b> <code>/rarityset &lt;num|name&gt; &lt;field&gt; &lt;value&gt;</code>\n"
            f"<b>Fields:</b> {', '.join(sorted(EDITABLE_FIELDS))}",
            parse_mode=enums.ParseMode.HTML,
        )
    label = _resolve_rarity(message.command[1])
    if not label:
        return await message.reply_text(f"❌ Unknown rarity: {html_escape(message.command[1])}")
    field = message.command[2].lower().strip()
    if field not in EDITABLE_FIELDS:
        return await message.reply_text(
            f"❌ Unknown field. Valid: {', '.join(sorted(EDITABLE_FIELDS))}"
        )
    try:
        value = int(message.command[3])
        if value < 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Value must be a non-negative integer.")

    changed = await set_rarity_field(label, field, value)
    if not changed:
        return await message.reply_text("⚠️ No change (value already set or rarity missing).")
    await message.reply_text(f"✅ {html_escape(label)}: <code>{field} = {value}</code>", parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("rarityadd") & sudo_filter)
@handle_errors
async def rarity_add_handler(_, message: types.Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "<b>Usage:</b> <code>/rarityadd &lt;num&gt; &lt;emoji Label&gt;</code>\n"
            "Example: <code>/rarityadd 26 🌸 Sakura</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    try:
        num = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Rarity number must be an integer.")
    label = " ".join(message.command[2:]).strip()
    error = await add_rarity(num, label)
    if error:
        return await message.reply_text(f"❌ {html_escape(error)}")
    await message.reply_text(
        f"✅ Added rarity <code>{num}</code> {html_escape(label)}.\n"
        "Weights start at 0 — set them with /rarityset to include it in pools.",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("rarityrefresh") & sudo_filter)
@handle_errors
async def rarity_refresh_handler(_, message: types.Message):
    try:
        count = await refresh_rarities()
    except Exception as e:
        return await message.reply_text(f"❌ Refresh failed: {html_escape(str(e))}")
    await message.reply_text(f"✅ Reloaded {count} rarities from database.")
