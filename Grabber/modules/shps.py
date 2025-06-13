import random
import logging
import aiohttp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import application, collection, user_collection

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SHOP_RARITY = "🪽 Shop"
DEFAULT_SHOP_PRICE = 50000
SHOP_PAGE_SIZE = 5
ADMIN_EXTOL_ADDRESS = "EXTAF9VYPP67bpFWJmw301503c4"
ADMINS = [7717913705]

EXTOL_API_BASE = 'https://marketapi.animerealms.org'


# === /balance command ===
async def balance_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or "extol_key" not in user_data:
        await update.message.reply_text("❌ Please register your Extol key with an admin.")
        return

    api_key = user_data["extol_key"]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{EXTOL_API_BASE}/api/balance", headers={"api-key": api_key}) as response:
                result = await response.json()
                if result.get("ok"):
                    balance = result.get("balance", 0)
                    address = result.get("address", "N/A")
                    await update.message.reply_text(
                        f"💰 *Your Extol Balance:* `{balance}` Extols\n"
                        f"🏦 *Address:* `{address}`",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(f"❌ Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Balance error: {e}")
            await update.message.reply_text("⚠️ Failed to fetch balance.")


# === Shop System ===
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

async def shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or "extol_key" not in user_data:
        await update.message.reply_text("❌ You are not registered or missing Extol key.")
        return

    shop_characters = await get_daily_shop_characters()
    if not shop_characters:
        await update.message.reply_text("🚫 No shop characters available.")
        return

    context.user_data["shop"] = shop_characters
    context.user_data["shop_page"] = 0

    balance = await fetch_user_balance(user_data["extol_key"])
    await send_shop_message(update, context, balance)

async def fetch_user_balance(api_key: str) -> int:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{EXTOL_API_BASE}/api/balance", headers={"api-key": api_key}) as response:
                result = await response.json()
                return result.get("balance", 0) if result.get("ok") else 0
        except:
            return 0

async def send_shop_message(update: Update, context: CallbackContext, balance: int) -> None:
    shop_characters = context.user_data.get("shop", [])
    page = context.user_data.get("shop_page", 0)

    if not shop_characters or page >= len(shop_characters):
        await update.message.reply_text("🚫 No characters available.")
        return

    character = shop_characters[page]
    price = character.get("price", DEFAULT_SHOP_PRICE)
    keyboard = [
        [InlineKeyboardButton("💰 Buy", callback_data=f"buy_{character['id']}")],
        [InlineKeyboardButton("⬅️ Prev", callback_data="shop_prev"), InlineKeyboardButton("➡️ Next", callback_data="shop_next")]
    ]
    text = (
        f"🛍️ *Character Shop*\n"
        f"💰 *Your Extol Balance:* {balance} Extols\n\n"
        f"🆔 *ID:* {character['id']}\n"
        f"📛 *Name:* {character['name']}\n"
        f"📺 *Anime:* {character['anime']}\n"
        f"🏷 *Rarity:* {character['rarity']}\n"
        f"💲 *Price:* {price} Extols"
    )
    if update.callback_query:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(character['img_url'], caption=text, parse_mode="Markdown"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_photo(photo=character["img_url"], caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def shop_navigation(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    action = query.data
    page = context.user_data.get("shop_page", 0)

    if "shop" not in context.user_data:
        await query.answer("❌ No shop data.", show_alert=True)
        return

    if action == "shop_prev":
        page = max(0, page - 1)
    elif action == "shop_next":
        page = min(len(context.user_data["shop"]) - 1, page + 1)

    context.user_data["shop_page"] = page
    user_data = await user_collection.find_one({"id": query.from_user.id})
    balance = await fetch_user_balance(user_data["extol_key"])
    await send_shop_message(update, context, balance)
    await query.answer()


# === Buying logic ===
async def buy_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]
    user_data = await user_collection.find_one({"id": user_id})

    if not user_data or "extol_key" not in user_data:
        await query.answer("❌ You are not registered or missing Extol key!", show_alert=True)
        return

    owned = user_data.get("characters", [])
    character = await collection.find_one({"id": character_id})

    if not character or character["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not found!", show_alert=True)
        return

    if any(c["id"] == character_id for c in owned):
        await query.answer("✅ Already owned!", show_alert=True)
        return

    price = character.get("price", DEFAULT_SHOP_PRICE)
    balance = await fetch_user_balance(user_data["extol_key"])
    if balance < price:
        await query.answer("❌ Not enough Extols!", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirm_{character_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    await query.message.reply_text(
        f"💰 *Price:* {price} Extols\n🛒 *Character:* {character['name']}\n\nConfirm purchase?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def confirm_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]
    user_data = await user_collection.find_one({"id": user_id})
    extol_key = user_data.get("extol_key")

    if not extol_key:
        await query.answer("❌ No Extol key registered!", show_alert=True)
        return

    character = await collection.find_one({"id": character_id})
    price = character.get("price", DEFAULT_SHOP_PRICE)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{EXTOL_API_BASE}/api/transfer",
            headers={"api-key": extol_key},
            json={"to": ADMIN_EXTOL_ADDRESS, "amount": price}
        ) as response:
            result = await response.json()
            if not result.get("ok"):
                await query.answer("❌ Payment failed.", show_alert=True)
                return

    character_data = {
        "id": character["id"],
        "name": character["name"],
        "anime": character["anime"],
        "rarity": character["rarity"],
        "img_url": character["img_url"]
    }

    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": character_data}}
    )

    await query.message.reply_text(
        f"✅ *Purchase Successful!*\n🎉 You now own *{character['name']}*\n💰 *Paid:* {price} Extols",
        parse_mode="Markdown"
    )
    await query.answer("✅ Success!")


async def cancel_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.message.reply_text("❌ Purchase cancelled.")
    await query.answer()


# === Admin command to set price ===
async def set_price(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ You are not an admin.")
        return
    try:
        char_id, price = context.args
        await collection.update_one({"id": char_id}, {"$set": {"price": int(price)}})
        await update.message.reply_text(f"✅ Price set: {char_id} → {price} Extols")
    except:
        await update.message.reply_text("❌ Usage: /setpr <id> <price>")


# === Handlers ===
application.add_handler(CommandHandler('shop', shop))
application.add_handler(CommandHandler('balance', balance_command))
application.add_handler(CommandHandler('setpr', set_price))
application.add_handler(CallbackQueryHandler(shop_navigation, pattern="^shop_(prev|next)$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern="^buy_"))
application.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_"))
application.add_handler(CallbackQueryHandler(cancel_purchase, pattern="^cancel$"))
    
