from pyrogram import errors, enums, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from Grabber import app
from Grabber.core.balance import update_user_balance
from Grabber.core.user import get_user_data, remove_char_from_user
from Grabber.core.utils import handle_errors, html_escape

SELL_PRICES = {
    "Common": 50,
    "Medium": 100,
    "Rare": 250,
    "Legendary": 500,
    "Cosmic": 1000,
    "Exclusive": 2000,
    "Limited Edition": 5000,
    "Royal": 10000
}

@app.on_message(filters.command("sell"))
@handle_errors
async def sell_handler(_, message: types.Message):
    if len(message.command) < 2:
        rates = "\n".join([f"{rarity}: <b>{price:,} ⬪</b>" for rarity, price in SELL_PRICES.items()])
        return await message.reply_text(
            f"<b>Usage:</b> <code>/sell &lt;id&gt;</code>\n\n"
            f"<b>Sell Rates:</b>\n{rates}",
            parse_mode=ParseMode.HTML
        )

    char_id = message.command[1]
    user_id = message.from_user.id

    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("<b>Your collection is empty.</b>", parse_mode=ParseMode.HTML)


    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await message.reply_text("<b>You don't own this character.</b>", parse_mode=ParseMode.HTML)

    rarity = char.get('rarity', 'Common')
    price = SELL_PRICES.get(rarity, 50)

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
        f"<b>Value:</b> <code>{price:,}</code> ⬪\n\n"
        f"<b>Current Balance:</b> <code>{current_shards:,}</code> ⬪\n"
        f"<b>New Balance:</b> <code>{new_shards:,}</code> ⬪\n\n"
        f"<i>Are you sure you want to sell this character?</i>"
    )

    await message.reply_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^sell_"))
async def sell_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split("_")
    action = data[1]

    # Handle both sell_c_{id}:{user_id} and sell_a:{user_id}
    parts = data[2].split(":") if len(data) > 2 else []
    if action == "a":
        owner_id = int(data[2].split(":")[1]) if ":" in data[2] else 0 # Fallback for old buttons
    else:
        owner_id = int(parts[1]) if len(parts) > 1 else 0

    if owner_id and query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)

    if action == "a":
        await query.message.edit_text("<b>Selling cancelled.</b>", parse_mode=ParseMode.HTML)
        return

    char_id = parts[0]
    user_id = query.from_user.id


    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await query.answer("Your collection is empty.", show_alert=True)

    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await query.answer("You don't own this character anymore.", show_alert=True)

    rarity = char.get('rarity', '⚪ Common')
    price = SELL_PRICES.get(rarity, 50)

    current_shards = user.get('balance', 0)
    new_shards = current_shards + price


    if await remove_char_from_user(user_id, char_id):
        await update_user_balance(user_id, price)
        await query.message.edit_text(
            f"<b>Successfully Sold!</b>\n\n"
            f"<b>Character:</b> {html_escape(char['name'])}\n"
            f"<b>Price:</b> <code>{price:,}</code> ⬪\n\n"
            f"<b>Your New Balance:</b> <code>{new_shards:,}</code> ⬪",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.answer("Failed to sell character.", show_alert=True)
