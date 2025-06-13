import random
import logging
import aiohttp
from pymongo import MongoClient
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import application, collection, user_collection  # Presumed MongoDB + bot app initialized
# === Configuration ===
EXTOL_API_KEY = "IAC-49ZENKUeYt"
EXTOL_RECEIVER = "EXTAF9VYPP67bpFWJmw301503c4"
SHOP_RARITY = "🪽 Shop"
DEFAULT_PRICE = 50  # Extols
SHOP_PAGE_SIZE = 5
ADMINS = [7717913705]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === MongoDB ===


# === Extol API ===
async def get_extol_balance():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://marketapi.animerealms.org/api/balance",
                               headers={"api-key": EXTOL_API_KEY}) as resp:
            return await resp.json()

async def withdraw_extol(amount, to):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://marketapi.animerealms.org/api/withdraw",
                               headers={"api-key": EXTOL_API_KEY},
                               params={"amount": amount, "address": to}) as resp:
            return await resp.json()

# === Character Shop ===
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

async def shop(update: Update, context: CallbackContext):
    chars = await get_daily_shop_characters()
    if not chars:
        await update.message.reply_text("🚫 No shop characters available.")
        return

    context.user_data["shop"] = chars
    context.user_data["shop_page"] = 0
    await send_shop_message(update, context)

async def send_shop_message(update: Update, context: CallbackContext):
    page = context.user_data.get("shop_page", 0)
    chars = context.user_data.get("shop", [])
    if page >= len(chars):
        await update.message.reply_text("🚫 Invalid page.")
        return

    char = chars[page]
    price = char.get("price", DEFAULT_PRICE)
    balance_data = await get_extol_balance()
    balance = balance_data.get("balance", 0)

    text = (
        f"🛍️ *Character Shop*\n"
        f"💰 *Extol Balance:* {balance} EXT\n\n"
        f"🆔 *ID:* {char['id']}\n"
        f"📛 *Name:* {char['name']}\n"
        f"📺 *Anime:* {char['anime']}\n"
        f"🏷 *Rarity:* {char['rarity']}\n"
        f"💲 *Price:* {price} EXT"
    )

    keyboard = [
        [InlineKeyboardButton("💰 Buy", callback_data=f"buy_{char['id']}")],
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="shop_prev"),
            InlineKeyboardButton("➡️ Next", callback_data="shop_next")
        ]
    ]

    if update.callback_query:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(media=char["img_url"], caption=text, parse_mode="Markdown"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_photo(
            photo=char["img_url"], caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

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

    if char_id in [c["id"] if isinstance(c, dict) else c for c in owned]:
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

async def set_price(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ You are not an admin.")
        return

    try:
        char_id, price = context.args
        await collection.update_one({"id": char_id}, {"$set": {"price": int(price)}})
        await update.message.reply_text(f"✅ Price updated: {char_id} → {price} EXT")
    except:
        await update.message.reply_text("❌ Use: /setpr <id> <price>")

# === Start Bot ===

application.add_handler(CommandHandler("shop", shop))
application.add_handler(CommandHandler("balances", balance_command))
application.add_handler(CommandHandler("setpr", set_price))
application.add_handler(CallbackQueryHandler(shop_navigation, pattern="^shop_(prev|next)$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern="^buy_"))

logger.info("Bot is running...")

    
