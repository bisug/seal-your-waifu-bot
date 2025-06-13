import random
import logging
import aiohttp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import application, collection, user_collection  # Presumed MongoDB + bot app initialized

# Constants
EXTOL_API_KEY = "IAC-49ZENKUeYt"
EXTOL_RECEIVER = "EXTAF9VYPP67bpFWJmw301503c4"
SHOP_RARITY = "🪽 Shop"
DEFAULT_PRICE = 50  # Extols
SHOP_PAGE_SIZE = 5
ADMINS = [7717913705]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# External API calls
async def get_extol_balance():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://marketapi.animerealms.org/api/balance", headers={"api-key": EXTOL_API_KEY}) as resp:
            return await resp.json()

async def withdraw_extol(amount, to):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://marketapi.animerealms.org/api/withdraw",
            headers={"api-key": EXTOL_API_KEY},
            params={"amount": amount, "address": to}
        ) as resp:
            return await resp.json()

# Load daily shop characters
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

# /shop command
async def shop(update: Update, context: CallbackContext):
    chars = await get_daily_shop_characters()
    if not chars:
        await update.message.reply_text("🚫 No shop characters available.")
        return

    context.user_data["shop"] = chars
    context.user_data["shop_page"] = 0
    await send_shop_message(update, context)

# Send shop character
async def send_shop_message(update: Update, context: CallbackContext):
    page = context.user_data.get("shop_page", 0)
    chars = context.user_data.get("shop", [])
    if page >= len(chars):
        await update.message.reply_text("🚫 Invalid page.")
        return

    character = chars[page]
    price = character.get("price", DEFAULT_PRICE)

    balance_data = await get_extol_balance()
    balance = balance_data.get("balance", 0)

    text = (
        f"🛍️ *Character Shop*\n"
        f"💰 *Extol Balance:* {balance} EXT\n\n"
        f"🆔 *ID:* {character['id']}\n"
        f"📛 *Name:* {character['name']}\n"
        f"📺 *Anime:* {character['anime']}\n"
        f"🏷 *Rarity:* {character['rarity']}\n"
        f"💲 *Price:* {price} EXT"
    )

    keyboard = [
        [InlineKeyboardButton("💰 Buy", callback_data=f"buy_{character['id']}")],
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="shop_prev"),
            InlineKeyboardButton("➡️ Next", callback_data="shop_next")
        ]
    ]

    if update.callback_query:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(media=character["img_url"], caption=text, parse_mode="Markdown"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_photo(
            photo=character["img_url"], caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

# Navigation buttons
async def shop_navigation(update: Update, context: CallbackContext):
    query = update.callback_query
    action = query.data
    page = context.user_data.get("shop_page", 0)

    if action == "shop_prev":
        context.user_data["shop_page"] = max(0, page - 1)
    elif action == "shop_next":
        context.user_data["shop_page"] = min(len(context.user_data["shop"]) - 1, page + 1)

    await send_shop_message(update, context)
    await query.answer()

# Buy character
async def buy_character(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    char_id = query.data.split("_")[1]

    user_data = await user_collection.find_one({"id": user_id}) or {}
    owned = user_data.get("characters", [])

    char = await collection.find_one({"id": char_id})
    if not char or char["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not available.", show_alert=True)
        return

    if any(c["id"] == char_id for c in owned):
        await query.answer("✅ You already own this character.", show_alert=True)
        return

    price = char.get("price", DEFAULT_PRICE)
    payment = await withdraw_extol(price, EXTOL_RECEIVER)

    if not payment.get("ok"):
        await query.answer(f"❌ Payment failed: {payment.get('error', 'unknown error')}", show_alert=True)
        return

    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"id": user_id},
            "$push": {"characters": {
                "id": char["id"],
                "name": char["name"],
                "anime": char["anime"],
                "rarity": char["rarity"],
                "img_url": char["img_url"]
            }}
        },
        upsert=True
    )

    await query.message.reply_text(
        f"✅ *Purchase Successful!*\n🎉 You now own *{char['name']}*!",
        parse_mode="Markdown"
    )
    await query.answer()

# /balance command
async def balance_command(update: Update, context: CallbackContext):
    data = await get_extol_balance()
    if not data or not data.get("ok"):
        await update.message.reply_text("❌ Could not retrieve balance.")
        return

    balance = data.get("balance", 0)
    address = data.get("address", "Unknown")
    await update.message.reply_text(
        f"💳 *Extol Balance:* {balance} EXT\n🏦 *Address:* `{address}`",
        parse_mode="Markdown"
    )

# Register handlers
application.add_handler(CommandHandler('shop', shop))
application.add_handler(CommandHandler('balance', balance_command))
application.add_handler(CallbackQueryHandler(shop_navigation, pattern="^shop_(prev|next)$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern="^buy_"))
