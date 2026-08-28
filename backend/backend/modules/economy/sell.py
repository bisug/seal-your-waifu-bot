import asyncio

from pyrogram import enums, filters, types

from backend import app
from backend.core.cache import sync_user_to_redis
from backend.core.roles import apply_role_bonus
from backend.core.user import get_user_data
from backend.core.utils import get_user_id_query, handle_errors, html_escape
from backend.database import user_collection

# Per-rarity liquidation value in SHARDS. Used by BOTH /sell and /recycle
# (the latter via get_sell_price) so dupe liquidation is consistent and every
# rarity is covered. High tiers are intentionally far below their shop (Zenith)
# price to keep Zenith scarce and prevent sell/rebuy arbitrage.
# Values now live in the `rarities` collection (see core/rarities.py); this
# is the same live dict, keyed by bare name ("Common").
from backend.core.rarities import SELL_PRICES  # noqa: E402

def normalize_sell_rarity(rarity: str) -> str:
    rarity_text = str(rarity or "Common")
    for key in SELL_PRICES:
        if rarity_text == key or key in rarity_text:
            return key
    return "Common"

def get_sell_price(rarity: str, user_id: int | None = None) -> int:
    base_price = SELL_PRICES.get(normalize_sell_rarity(rarity), SELL_PRICES["Common"])
    if user_id is None:
        return base_price
    price, _ = apply_role_bonus(user_id, base_price, "sell_bonus_percent")
    return price


def get_sell_price_details(rarity: str, user_id: int | None = None) -> tuple[int, int]:
    base_price = SELL_PRICES.get(normalize_sell_rarity(rarity), SELL_PRICES["Common"])
    if user_id is None:
        return base_price, 0
    return apply_role_bonus(user_id, base_price, "sell_bonus_percent")

async def sell_character_from_user(user_id: int, char_id: str):
    for _ in range(3):
        user = await user_collection.find_one(get_user_id_query(user_id))
        if not user or not user.get("characters"):
            return None

        chars = user["characters"]
        idx_to_remove = next((i for i, c in enumerate(chars) if str(c.get("id")) == str(char_id)), -1)
        if idx_to_remove == -1:
            return None

        char = chars[idx_to_remove]
        # Lock guard lives in the shared seller so BOTH the bot callback and
        # the WebApp routes honor /lock (previously only /sell checked).
        if str(char.get("id")) in (user.get("locked") or []):
            return None

        price = get_sell_price(char.get("rarity", "Common"), user_id)
        new_chars = chars[:idx_to_remove] + chars[idx_to_remove + 1:]
        current_version = user.get("version", 0)
        current_count = user.get("char_count", len(chars))
        new_count = max(0, current_count - 1)
        new_balance = user.get("balance", 0) + price

        update_filter = get_user_id_query(user_id)
        update_filter["version"] = current_version
        result = await user_collection.update_one(
            update_filter,
            {
                "$set": {"characters": new_chars, "char_count": new_count},
                "$inc": {"balance": price, "version": 1}
            }
        )
        if result.modified_count > 0:
            await sync_user_to_redis(user_id)
            return char, price, new_balance

        await asyncio.sleep(0.1)
    return None

@app.on_message(filters.command("sell"))
@handle_errors
async def sell_handler(_, message: types.Message):
    if len(message.command) < 2:
        rates = "\n".join([f"{rarity}: <b>{price:,} ⬪</b>" for rarity, price in SELL_PRICES.items()])
        return await message.reply_text(
            f"<b>Usage:</b> <code>/sell &lt;id&gt;</code>\n\n"
            f"<b>Sell Rates:</b>\n{rates}",
            parse_mode=enums.ParseMode.HTML
        )
    char_id = message.command[1]
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("<b>Your collection is empty.</b>", parse_mode=enums.ParseMode.HTML)
    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await message.reply_text("<b>You don't own this character.</b>", parse_mode=enums.ParseMode.HTML)
    if str(char_id) in (user.get('locked') or []):
        return await message.reply_text("🔒 This character is locked. Unlock it with <code>/unlock &lt;id&gt;</code> first.", parse_mode=enums.ParseMode.HTML)
    rarity = char.get('rarity', 'Common')
    price, staff_bonus = get_sell_price_details(rarity, user_id)
    buttons = [
        [
            types.InlineKeyboardButton("Confirm", callback_data=f"sell_c_{char_id}:{user_id}"),
            types.InlineKeyboardButton("Cancel", callback_data=f"sell_a:{user_id}")
        ]
    ]
    current_shards = user.get('balance', 0)
    new_shards = current_shards + price
    confirmation_text = (
        f"<b>Sell Confirmation</b>\n\n"
        f"<b>Character:</b> {html_escape(char['name'])}\n"
        f"<b>Rarity:</b> {html_escape(rarity)}\n"
        f"<b>Value:</b> <code>{price:,}</code> ⬪"
        f"{f' (+{staff_bonus:,} staff)' if staff_bonus else ''}\n\n"
        f"<b>Current Balance:</b> <code>{current_shards:,}</code> ⬪\n"
        f"<b>New Balance:</b> <code>{new_shards:,}</code> ⬪\n\n"
        f"<i>Are you sure you want to sell this character?</i>"
    )
    await message.reply_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
@app.on_callback_query(filters.regex(r"^sell_"))
async def sell_callback_handler(_, query: types.CallbackQuery):
    # Cancel buttons are "sell_a:{user_id}" (one underscore segment), confirms
    # are "sell_c_{char_id}:{user_id}". Handle the cancel shape first — the
    # old split("_") parser produced action="a:123" and crashed on parts[0].
    tail = query.data.split("_", 1)[1]
    if tail.startswith("a:"):
        try:
            owner_id = int(tail.split(":", 1)[1])
        except (IndexError, ValueError):
            owner_id = 0
        if owner_id and query.from_user.id != owner_id:
            return await query.answer("This is not your menu!", show_alert=True)
        await query.message.edit_text("<b>Selling cancelled.</b>", parse_mode=enums.ParseMode.HTML)
        return

    data = query.data.split("_")
    parts = data[2].split(":") if len(data) > 2 else []
    owner_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    if owner_id and query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)
    if not parts:
        return await query.answer("Invalid sell request.", show_alert=True)
    char_id = parts[0]
    user_id = query.from_user.id
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await query.answer("Your collection is empty.", show_alert=True)
    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await query.answer("You don't own this character anymore.", show_alert=True)
    if str(char_id) in (user.get('locked') or []):
        return await query.answer("🔒 This character is locked. Unlock it first.", show_alert=True)
    rarity = char.get('rarity', '⚪ Common')
    price = get_sell_price(rarity, user_id)
    current_shards = user.get('balance', 0)
    new_shards = current_shards + price
    sale = await sell_character_from_user(user_id, char_id)
    if sale:
        sold_char, price, new_shards = sale
        await query.message.edit_text(
            f"<b>Successfully Sold!</b>\n\n"
            f"<b>Character:</b> {html_escape(sold_char['name'])}\n"
            f"<b>Price:</b> <code>{price:,}</code> ⬪\n\n"
            f"<b>Your New Balance:</b> <code>{new_shards:,}</code> ⬪",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.answer("Failed to sell character.", show_alert=True)
