import random
import logging
import aiohttp
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
)
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, CallbackContext
)
from Grabber import application, collection, user_collection

# === CONFIG ===
EXTOL_API_KEY = 'IAC-49ZENKUeYt'
EXTOL_API_BASE = 'https://marketapi.animerealms.org'
BOT_EXTOL_ADDRESS = 'EXTAF9VYPP67bpFWJmw301503c4'

SHOP_RARITY = "🪽 Shop"
DEFAULT_SHOP_PRICE = 50000
SHOP_PAGE_SIZE = 5
ADMINS = [7717913705]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === EXTOL API HELPERS ===
async def create_payment_link(address: str, amount: float):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{EXTOL_API_BASE}/api/create-payment",
            headers={"api-key": EXTOL_API_KEY},
            json={"address": address, "amount": amount}
        ) as resp:
            return await resp.json()

async def check_payment_status(payment_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{EXTOL_API_BASE}/api/payment-status",
            headers={"api-key": EXTOL_API_KEY},
            params={"payment_id": payment_id}
        ) as resp:
            return await resp.json()

# === SHOP FUNCTIONS ===
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

async def shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({"id": user_id}) or {}

    if not user_data:
        await update.message.reply_text("❌ You are not registered! Start collecting characters first.")
        return

    shop_characters = await get_daily_shop_characters()
    if not shop_characters:
        await update.message.reply_text("🚫 No shop characters available today.")
        return

    context.user_data["shop"] = shop_characters
    context.user_data["shop_page"] = 0
    await send_shop_message(update, context)

async def send_shop_message(update: Update, context: CallbackContext) -> None:
    shop_characters = context.user_data.get("shop", [])
    page = context.user_data.get("shop_page", 0)

    if not shop_characters or page >= len(shop_characters):
        await update.message.reply_text("🚫 No characters available.")
        return

    character = shop_characters[page]
    price = character.get("price", DEFAULT_SHOP_PRICE)
    extol_price = round(price / 1000, 2)

    keyboard = [
        [InlineKeyboardButton("💰 Buy", callback_data=f"buy_{character['id']}")],
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="shop_prev"),
            InlineKeyboardButton("➡️ Next", callback_data="shop_next")
        ]
    ]

    text = (
        f"🛍️ **Character Shop**\n"
        f"💲 **Price:** {extol_price} Extols\n\n"
        f"🆔 **ID:** {character['id']}\n"
        f"📛 **Name:** {character['name']}\n"
        f"📺 **Anime:** {character['anime']}\n"
        f"🏷 **Rarity:** {character['rarity']}"
    )

    if update.callback_query:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(
                media=character["img_url"],
                caption=text,
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_photo(
            photo=character["img_url"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def shop_navigation(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    action = query.data

    if "shop" not in context.user_data:
        await query.answer("❌ No shop data available.", show_alert=True)
        return

    page = context.user_data.get("shop_page", 0)
    if action == "shop_prev":
        page = max(0, page - 1)
    elif action == "shop_next":
        page = min(len(context.user_data["shop"]) - 1, page + 1)

    context.user_data["shop_page"] = page
    await send_shop_message(update, context)
    await query.answer()

# === BUY FLOW ===
async def buy_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]

    user_data = await user_collection.find_one({"id": user_id}) or {}
    owned = [c["id"] for c in user_data.get("characters", [])]

    character = await collection.find_one({"id": character_id})
    if not character or character["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not found!", show_alert=True)
        return

    if character["id"] in owned:
        await query.answer("✅ You already own this character!", show_alert=True)
        return

    price = round(character.get("price", DEFAULT_SHOP_PRICE) / 1000, 2)

    payment = await create_payment_link(BOT_EXTOL_ADDRESS, price)
    if not payment.get("ok"):
        await query.answer("❌ Payment error!", show_alert=True)
        return

    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"pending_payments": {
            "payment_id": payment["payment_id"],
            "character_id": character["id"]
        }}},
        upsert=True
    )

    await query.message.reply_text(
        f"🛒 To buy **{character['name']}**, pay {price} Extols:\n"
        f"[🔗 Click here to pay]({payment['payment_url']})\n\n"
        f"After paying, send /claimshop to confirm.",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await query.answer("💰 Payment link created!")

async def claim_shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({"id": user_id}) or {}
    pending = user_data.get("pending_payments", [])

    if not pending:
        await update.message.reply_text("❌ No pending payments.")
        return

    for entry in pending:
        status = await check_payment_status(entry["payment_id"])
        if status.get("ok") and status["status"] == "paid":
            character = await collection.find_one({"id": entry["character_id"]})
            if not character:
                continue

            char_data = {
                "id": character["id"],
                "name": character["name"],
                "anime": character["anime"],
                "rarity": character["rarity"],
                "img_url": character["img_url"]
            }

            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"characters": char_data},
                    "$pull": {"pending_payments": {"payment_id": entry["payment_id"]}}
                }
            )

            await update.message.reply_text(
                f"✅ Payment confirmed! You received **{character['name']}**.",
                parse_mode="Markdown"
            )
            return

    await update.message.reply_text("⏳ No confirmed payments yet. Try again shortly.")

# === ADMIN ===
async def set_price(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ You are not an admin.")
        return

    try:
        character_id, price = context.args
        price = int(price)
        await collection.update_one({"id": character_id}, {"$set": {"price": price}})
        await update.message.reply_text(f"✅ Price updated: **{character_id}** → {price} coins")
    except:
        await update.message.reply_text("❌ Invalid format. Use `/setpr id price`.")

# === CANCEL HANDLER ===
async def cancel_purchase(update: Update, context: CallbackContext) -> None:
    await update.callback_query.message.reply_text("❌ Purchase cancelled.")
    await update.callback_query.answer()

# === HANDLERS ===
application.add_handler(CommandHandler('shop', shop))
application.add_handler(CommandHandler('setpr', set_price))
application.add_handler(CommandHandler('claimshop', claim_shop))

application.add_handler(CallbackQueryHandler(shop_navigation, pattern="^shop_(prev|next)$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern="^buy_"))
application.add_handler(CallbackQueryHandler(cancel_purchase, pattern="^cancel$"))
