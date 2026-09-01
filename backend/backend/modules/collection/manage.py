from pyrogram import enums, filters, types

from backend.client import app
from backend.core.user import get_user_data, remove_char_from_user, update_user
from backend.core.utils import handle_errors, html_escape
from backend.database import collection
from backend.modules.economy.sell import get_sell_price

HTML = enums.ParseMode.HTML


def _owns(user: dict, char_id: str) -> dict | None:
    for c in user.get("characters", []):
        if isinstance(c, dict) and str(c.get("id")) == str(char_id):
            return c
    return None


# ── Character lock ──────────────────────────────────────────────────────────
# Protects a character from being traded or sold. Owners may still fuse their
# own duplicates voluntarily.
@app.on_message(filters.command(["lock", "unlock"]))
@handle_errors
async def lock_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b> <code>/lock &lt;id&gt;</code> or <code>/unlock &lt;id&gt;</code>",
            parse_mode=HTML,
        )
    char_id = str(message.command[1])
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    if not _owns(user or {}, char_id):
        return await message.reply_text("❌ You don't own this character.", parse_mode=HTML)
    locked = (message.command[0].lower() == "lock")
    op = {"$addToSet": {"locked": char_id}} if locked else {"$pull": {"locked": char_id}}
    await update_user(user_id, op)
    char = _owns(user, char_id)
    name = html_escape(char.get("name", "Unknown")) if char else char_id
    await message.reply_text(
        f"{'🔒' if locked else '🔓'} <b>{name}</b> "
        f"{'locked' if locked else 'unlocked'}.",
        parse_mode=HTML,
    )


@app.on_message(filters.command(["locks", "locklist"]))
@handle_errors
async def locks_handler(_, message: types.Message):
    user = await get_user_data(message.from_user.id)
    locked = (user or {}).get("locked", [])
    if not locked:
        return await message.reply_text("🔓 You have no locked characters.", parse_mode=HTML)
    lines = []
    for cid in locked:
        char = _owns(user, cid)
        if char:
            lines.append(f"• <code>{cid}</code> — {html_escape(char.get('name', 'Unknown'))}")
    if not lines:
        return await message.reply_text("🔓 You have no locked characters.", parse_mode=HTML)
    await message.reply_text(
        f"<b>🔒 Locked Characters ({len(lines)})</b>\n\n" + "\n".join(lines),
        parse_mode=HTML,
    )


# ── Wishlist ───────────────────────────────────────────────────────────────
@app.on_message(filters.command(["wishlist", "wl"]))
@handle_errors
async def wishlist_handler(_, message: types.Message):
    user_id = message.from_user.id
    args = message.command[1:] if len(message.command) > 1 else []
    sub = args[0].lower() if args else "list"

    if sub in ("add", "a"):
        if len(args) < 2:
            return await message.reply_text("<b>Usage:</b> <code>/wishlist add &lt;id&gt;</code>", parse_mode=HTML)
        char_id = str(args[1])
        char = await collection.find_one({"id": char_id})
        if not char:
            return await message.reply_text("❌ Character not found in the catalog.", parse_mode=HTML)
        await update_user(user_id, {"$addToSet": {"wishlist": char_id}})
        await message.reply_text(
            f"➕ Added <b>{html_escape(char.get('name', 'Unknown'))}</b> to your wishlist.",
            parse_mode=HTML,
        )
        return

    if sub in ("del", "remove", "r"):
        if len(args) < 2:
            return await message.reply_text("<b>Usage:</b> <code>/wishlist del &lt;id&gt;</code>", parse_mode=HTML)
        char_id = str(args[1])
        await update_user(user_id, {"$pull": {"wishlist": char_id}})
        await message.reply_text(f"➖ Removed <code>{char_id}</code> from your wishlist.", parse_mode=HTML)
        return

    # list
    user = await get_user_data(user_id)
    wl = (user or {}).get("wishlist", [])
    if not wl:
        return await message.reply_text(
            "💡 Your wishlist is empty.\nUse <code>/wishlist add &lt;id&gt;</code> to track characters you want.",
            parse_mode=HTML,
        )
    own_ids = {str(c.get("id")) for c in (user or {}).get("characters", [])}
    lines, owned = [], 0
    for cid in wl:
        char = await collection.find_one({"id": cid})
        if not char:
            continue
        have = cid in own_ids
        owned += 1 if have else 0
        tag = "✅ have" if have else "❌ need"
        lines.append(
            f"• <code>{cid}</code> — {html_escape(char.get('name', 'Unknown'))} "
            f"[{html_escape(str(char.get('rarity', 'Common')))}] {tag}"
        )
    if not lines:
        return await message.reply_text("💡 Your wishlist is empty.", parse_mode=HTML)
    await message.reply_text(
        f"<b>💡 Wishlist ({owned}/{len(lines)} owned)</b>\n\n" + "\n".join(lines),
        parse_mode=HTML,
    )


# ── Fuse duplicate copies into shards ──────────────────────────────────────
@app.on_message(filters.command("fuse"))
@handle_errors
async def fuse_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b> <code>/fuse &lt;id&gt; [count]</code>\n"
            "Converts duplicate copies (you keep 1) into shards.",
            parse_mode=HTML,
        )
    char_id = str(message.command[1])
    requested = None
    if len(message.command) >= 3:
        try:
            requested = int(message.command[2])
        except ValueError:
            return await message.reply_text("❌ Count must be a number.", parse_mode=HTML)
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    copies = [c for c in (user or {}).get("characters", []) if str(c.get("id")) == char_id]
    if not copies:
        return await message.reply_text("❌ You don't own this character.", parse_mode=HTML)
    if len(copies) < 2:
        return await message.reply_text("❌ Need at least 2 copies to fuse (you keep 1).", parse_mode=HTML)
    fusable = len(copies) - 1
    to_fuse = min(requested, fusable) if requested else fusable
    if to_fuse < 1:
        return await message.reply_text("❌ Nothing to fuse.", parse_mode=HTML)

    rarity = copies[0].get("rarity", "Common")
    name = copies[0].get("name", "Unknown")
    earned = 0
    for _ in range(to_fuse):
        if not await remove_char_from_user(user_id, char_id):
            break
        earned += get_sell_price(rarity, user_id)
    if earned == 0:
        return await message.reply_text("❌ Nothing was fused.", parse_mode=HTML)
    await update_user(user_id, {"$inc": {"balance": earned}})
    await message.reply_text(
        f"<b>⚗️ Fused {to_fuse} duplicate(s)!</b>\n\n"
        f"<b>Character:</b> {html_escape(name)}\n"
        f"<b>Earned:</b> <code>{earned:,}</code> ⬪",
        parse_mode=HTML,
    )
