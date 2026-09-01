import uuid

from pyrogram import enums, filters, types

from backend import sudo_filter
from backend.client import app
from backend.core.rarities import (
    EDITABLE_FIELDS,
    NUMERIC_FIELDS,
    RARITY_MAP,
    add_rarity,
    get_rarity_docs,
    rarity_id_of,
    refresh_rarities,
    rename_rarity,
    set_rarity_field,
)
from backend.core.utils import handle_errors, html_escape

# Pending rename proposals: proposal_id -> (rarity_id, emoji, name)
_pending_renames: dict[str, tuple[int, str, str]] = {}


@app.on_message(filters.command("rarityconfig") & sudo_filter)
@handle_errors
async def rarity_config_handler(_, message: types.Message):
    lines = [
        "<b>Rarity Config (DB-backed, by rarity_id)</b>",
        "<i>id · label · spawn/active/shop/claim weights · price ⧫ · stock · sell ⬪ · milestone</i>",
        "",
    ]
    for doc in get_rarity_docs():
        lines.append(
            f"<code>{doc['_id']}</code> {html_escape(doc.get('emoji', ''))} "
            f"{html_escape(doc.get('name', ''))} — "
            f"w:{doc.get('spawn_weight')}/{doc.get('active_spawn_weight')}/"
            f"{doc.get('shop_weight')}/{doc.get('claim_weight')} · "
            f"{doc.get('shop_price')}⧫ · stock {doc.get('stock_limit')} · "
            f"sell {doc.get('sell_price')}⬪ · ms {doc.get('milestone', 0)}"
        )
    lines.extend([
        "",
        "<b>Edit:</b> <code>/rarityset &lt;id|name&gt; &lt;field&gt; &lt;value&gt;</code>",
        f"<b>Fields:</b> {', '.join(sorted(EDITABLE_FIELDS))}",
        "<b>Add:</b> <code>/rarityadd &lt;id&gt; &lt;emoji&gt; &lt;Name&gt;</code>",
        "<b>Rename:</b> <code>/rarityrename &lt;id|name&gt; &lt;emoji&gt; &lt;New Name&gt;</code>",
        "<b>Reload:</b> <code>/rarityrefresh</code>",
    ])
    await message.reply_text("\n".join(lines), parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("rarityset") & sudo_filter)
@handle_errors
async def rarity_set_handler(_, message: types.Message):
    if len(message.command) < 4:
        return await message.reply_text(
            "<b>Usage:</b> <code>/rarityset &lt;id|name&gt; &lt;field&gt; &lt;value&gt;</code>\n"
            f"<b>Fields:</b> {', '.join(sorted(EDITABLE_FIELDS))}",
            parse_mode=enums.ParseMode.HTML,
        )
    rarity_id = rarity_id_of(message.command[1])
    if rarity_id is None:
        return await message.reply_text(f"❌ Unknown rarity: {html_escape(message.command[1])}")
    field = message.command[2].lower().strip()
    if field not in EDITABLE_FIELDS:
        return await message.reply_text(
            f"❌ Unknown field. Valid: {', '.join(sorted(EDITABLE_FIELDS))}"
        )
    if field in NUMERIC_FIELDS:
        try:
            value = int(message.command[3])
            if value < 0:
                raise ValueError
        except ValueError:
            return await message.reply_text("❌ Value must be a non-negative integer.")
    else:
        value = " ".join(message.command[3:]).strip()
        if not value:
            return await message.reply_text("❌ Value cannot be empty.")

    changed = await set_rarity_field(rarity_id, field, value)
    if not changed:
        return await message.reply_text("⚠️ No change (value already set or rarity missing).")
    await message.reply_text(
        f"✅ {html_escape(RARITY_MAP.get(rarity_id, str(rarity_id)))}: "
        f"<code>{field} = {html_escape(str(value))}</code>",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("rarityadd") & sudo_filter)
@handle_errors
async def rarity_add_handler(_, message: types.Message):
    if len(message.command) < 4:
        return await message.reply_text(
            "<b>Usage:</b> <code>/rarityadd &lt;id&gt; &lt;emoji&gt; &lt;Name&gt;</code>\n"
            "Example: <code>/rarityadd 26 🌸 Sakura</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    try:
        rarity_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Rarity id must be an integer.")
    emoji = message.command[2].strip()
    name = " ".join(message.command[3:]).strip()
    error = await add_rarity(rarity_id, emoji, name)
    if error:
        return await message.reply_text(f"❌ {html_escape(error)}")
    await message.reply_text(
        f"✅ Added rarity <code>{rarity_id}</code> {html_escape(emoji)} {html_escape(name)}.\n"
        "Weights start at 0 — set them with /rarityset to include it in pools.",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("rarityrename") & sudo_filter)
@handle_errors
async def rarity_rename_handler(_, message: types.Message):
    if len(message.command) < 4:
        return await message.reply_text(
            "<b>Usage:</b> <code>/rarityrename &lt;id|name&gt; &lt;emoji&gt; &lt;New Name&gt;</code>\n"
            "Example: <code>/rarityrename 3 🟠 Ultra Rare</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    rarity_id = rarity_id_of(message.command[1])
    if rarity_id is None:
        return await message.reply_text(f"❌ Unknown rarity: {html_escape(message.command[1])}")
    emoji = message.command[2].strip()
    name = " ".join(message.command[3:]).strip()
    old_label = RARITY_MAP.get(rarity_id, "?")
    new_label = f"{emoji} {name}".strip()

    proposal_id = str(uuid.uuid4())[:8]
    _pending_renames[proposal_id] = (rarity_id, emoji, name)

    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"rren_ok:{proposal_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"rren_no:{proposal_id}"),
        ]
    ])
    await message.reply_text(
        f"<b>Rename rarity {rarity_id}?</b>\n\n"
        f"{html_escape(old_label)}  ➜  {html_escape(new_label)}\n\n"
        "This updates the rarity table and propagates the new label to all "
        "character docs and user harems.",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex(r"^rren_(ok|no):([0-9a-f]{8})$"))
@handle_errors
async def rarity_rename_callback(_, query: types.CallbackQuery):
    action, proposal_id = query.data.split(":")
    pending = _pending_renames.pop(proposal_id, None)
    if not pending:
        return await query.answer("Proposal expired.", show_alert=True)
    if action == "no":
        await query.answer("Cancelled.")
        return await query.message.edit_text("❌ Rarity rename cancelled.")

    rarity_id, emoji, name = pending
    await query.answer("Renaming...")
    result = await rename_rarity(rarity_id, emoji, name)
    if not result:
        return await query.message.edit_text("❌ Rarity no longer exists.")
    old_label, new_label = result
    await query.message.edit_text(
        f"✅ Renamed {html_escape(old_label)} ➜ {html_escape(new_label)}",
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
