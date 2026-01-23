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
        return await message.reply_text("❌ Usage: `/sell <id>`")

    char_id = message.command[1]
    user_id = message.from_user.id
    
    user = await get_user_data(user_id)
    if not user or not user.get('characters'):
        return await message.reply_text("❌ Your collection is empty.")

    # Find character to get rarity
    char = next((c for c in user['characters'] if str(c.get('id')) == char_id), None)
    if not char:
        return await message.reply_text("❌ You don't own this character.")

    rarity = char.get('rarity', '⚪ Common')
    price = SELL_PRICES.get(rarity, 50)

    # Atomic removal
    if await remove_char_from_user(user_id, char_id):
        await update_user_balance(user_id, price)
        await message.reply_text(f"✅ Sold **{char['name']}** for 💵 **{price}** coins!")
    else:
        await message.reply_text("❌ Failed to sell character.")
