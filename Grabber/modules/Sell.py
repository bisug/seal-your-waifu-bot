from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber.core.user import get_user_data, remove_char_from_user
from Grabber.core.game import update_user_balance

SELL_PRICES = {
    "⚪ Common": 50,
    "🟢 Medium": 100,
    "🟠 Rare": 250,
    "🟡 Legendary": 500,
    "💠 Cosmic": 1000,
    "💮 Exclusive": 2000,
    "🔮 Limited Edition": 5000,
    "🫧 Royal": 10000
}

@app.on_message(filters.command("sell"))
async def sell_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ <b>Usage:</b> <code>/sell &lt;id&gt;</code>", parse_mode=enums.ParseMode.HTML)

    char_id = message.command[1]
    user_id = message.from_user.id
    
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("❌ <b>Your collection is empty.</b>", parse_mode=enums.ParseMode.HTML)

    # Find character to get details
    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await message.reply_text("❌ <b>You don't own this character.</b>", parse_mode=enums.ParseMode.HTML)

    rarity = char.get('rarity', '⚪ Common')
    price = SELL_PRICES.get(rarity, 50)

    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"sell_c_{char_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="sell_a")
        ]
    ]
    
    await message.reply_text(
        f"<b>Selling:</b> {char['name']}\n"
        f"<b>Rarity:</b> {rarity}\n"
        f"<b>Value:</b> 💵 {price} coins\n\n"
        "<i>Are you sure you want to sell this character?</i>",
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@app.on_callback_query(filters.regex(r"^sell_"))
async def sell_callback_handler(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]

    if action == "a":
        await query.message.edit_text("❌ <b>Selling cancelled.</b>", parse_mode=enums.ParseMode.HTML)
        return

    char_id = data[2]
    
    # Re-verify ownership to prevent race conditions or exploits
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await query.answer("❌ Your collection is empty.", show_alert=True)

    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await query.answer("❌ You don't own this character anymore.", show_alert=True)

    rarity = char.get('rarity', '⚪ Common')
    price = SELL_PRICES.get(rarity, 50)

    # Atomic removal
    if await remove_char_from_user(user_id, char_id):
        await update_user_balance(user_id, price)
        await query.message.edit_text(
            f"✅ <b>Successfully Sold!</b>\n\n"
            f"<b>Character:</b> {char['name']}\n"
            f"<b>Price:</b> 💵 {price} coins balance updated!",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.answer("❌ Failed to sell character.", show_alert=True)
