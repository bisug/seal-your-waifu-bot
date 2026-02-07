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
        rates = "\n".join([f"{rarity}: **{price:,} ⬪**" for rarity, price in SELL_PRICES.items()])
        return await message.reply_text(
            f"❌ **Usage:** `/sell <id>`\n\n"
            f"💰 **Sell Rates:**\n{rates}",
            parse_mode=enums.ParseMode.MARKDOWN
        )

    char_id = message.command[1]
    user_id = message.from_user.id
    
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("❌ **Your collection is empty.**", parse_mode=enums.ParseMode.MARKDOWN)

    # Find character to get details
    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await message.reply_text("❌ **You don't own this character.**", parse_mode=enums.ParseMode.MARKDOWN)

    rarity = char.get('rarity', '⚪ Common')
    price = SELL_PRICES.get(rarity, 50)

    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"sell_c_{char_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="sell_a")
        ]
    ]
    
    current_shards = user.get('balance', 0)
    new_shards = current_shards + price
    
    confirmation_text = (
        f"💰 **Sell Confirmation**\n\n"
        f"**Character:** {char['name']}\n"
        f"**Rarity:** {rarity}\n"
        f"**Value:** {price:,} ⬪\n\n"
        f"**Current Balance:** {current_shards:,} ⬪\n"
        f"**New Balance:** {new_shards:,} ⬪\n\n"
        f"_Are you sure you want to sell this character?_"
    )
    
    await message.reply_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_callback_query(filters.regex(r"^sell_"))
async def sell_callback_handler(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]

    if action == "a":
        await query.message.edit_text("❌ **Selling cancelled.**", parse_mode=enums.ParseMode.MARKDOWN)
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

    current_shards = user.get('balance', 0)
    new_shards = current_shards + price

    # Atomic removal
    if await remove_char_from_user(user_id, char_id):
        await update_user_balance(user_id, price)
        await query.message.edit_text(
            f"✅ **Successfully Sold!**\n\n"
            f"**Character:** {char['name']}\n"
            f"**Price:** {price:,} ⬪\n\n"
            f"**Your New Balance:** {new_shards:,} ⬪",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await query.answer("❌ Failed to sell character.", show_alert=True)
