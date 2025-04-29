import random
import logging
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
)
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import application, collection, user_collection

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SHOP_RARITY = "🪽 Shop"
DEFAULT_SHOP_PRICE = 50000  
SHOP_PAGE_SIZE = 5  
ADMINS = [7717913705]  

# Fetch a random selection of shop characters
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

# Command: /shop
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
    await send_shop_message(update, context, user_data.get("balance", 0))

# Send shop message
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
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="shop_prev"),
            InlineKeyboardButton("➡️ Next", callback_data="shop_next")
        ]
    ]

    text = (
        f"🛍️ **Character Shop**\n"
        f"💰 **Your Balance:** {balance} coins\n\n"
        f"🆔 **ID:** {character['id']}\n"
        f"📛 **Name:** {character['name']}\n"
        f"📺 **Anime:** {character['anime']}\n"
        f"🏷 **Rarity:** {character['rarity']}\n"
        f"💲 **Price:** {price} coins"
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

# Shop navigation
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
    user_data = await user_collection.find_one({"id": query.from_user.id}) or {}
    balance = user_data.get("balance", 0)

    await send_shop_message(update, context, balance)
    await query.answer()

# Buy character
async def buy_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]

    user_data = await user_collection.find_one({"id": user_id}) or {}
    balance = user_data.get("balance", 0)
    owned_characters = user_data.get("characters", [])

    character = await collection.find_one({"id": character_id})
    if not character or character["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not found!", show_alert=True)
        return

    if character_id in owned_characters:
        await query.answer("✅ You already own this character!", show_alert=True)
        return

    price = character.get("price", DEFAULT_SHOP_PRICE)
    if balance < price:
        await query.answer("❌ Not enough coins!", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirm_{character_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]

    await query.message.reply_text(
        f"💰 **Price:** {price} coins\n🛒 **Character:** {character['name']}\n\nConfirm purchase?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Confirm purchase
async def confirm_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    character_id = query.data.split("_")[1]

    user_data = await user_collection.find_one({"id": user_id}) or {}
    balance = user_data.get("balance", 0)
    owned_characters = user_data.get("characters", [])

    character = await collection.find_one({"id": character_id})
    if not character or character["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not found!", show_alert=True)
        return

    price = character.get("price", DEFAULT_SHOP_PRICE)
    if balance < price:
        await query.answer("❌ Not enough coins!", show_alert=True)
        return

    new_balance = balance - price

    # Append full character data instead of just the ID
    character_data = {
        "id": character["id"],
        "name": character["name"],
        "anime": character["anime"],
        "rarity": character["rarity"],
        "img_url": character["img_url"]
    }

    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"balance": new_balance},
            "$push": {"characters": character_data}  # Push full character data
        }
    )

    await query.message.reply_text(
        f"✅ **Purchase Successful!**\n🎉 You now own **{character['name']}**!\n💰 **Remaining Balance:** {new_balance} coins",
        parse_mode="Markdown"
    )
    
    await query.answer("✅ Purchase successful!")


# Cancel purchase
async def cancel_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.message.reply_text("❌ Purchase cancelled.")
    await query.answer()

# Admin command: /setpr (Set Price)
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

# Handlers
application.add_handler(CommandHandler('shop', shop))
application.add_handler(CommandHandler('setpr', set_price))
application.add_handler(CallbackQueryHandler(shop_navigation, pattern="^shop_(prev|next)$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern="^buy_"))
application.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_"))
application.add_handler(CallbackQueryHandler(cancel_purchase, pattern="^cancel$"))
    
