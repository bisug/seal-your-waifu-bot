import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from Grabber import user_collection, application

# Default Pet
DEFAULT_PET = {
    "name": "Fluffy Fox 🦊",
    "luck": 0.10,
    "owned": True,
    "img": "https://i.ibb.co/6JwW7b7D/file-81.jpg"
}

# Pet Shop List
PET_SHOP = [
    {"name": "Blaze Fang 🐺", "luck": 0.15, "price": 10000, "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg"},
    {"name": "Mystic Dragon 🐲", "luck": 0.25, "price": 25000, "img": "https://files.catbox.moe/7kvcqj.jpg"},
    {"name": "Shadow Panther 🐆", "luck": 0.35, "price": 50000, "img": "https://i.ibb.co/8CdC5QG/file-86.jpg"},
    {"name": "Cosmic Phoenix 🦅", "luck": 0.50, "price": 100000, "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg"},
]

# Send Pet Shop Page
async def send_petshop_page(update: Update, context: CallbackContext, page: int):
    pet = PET_SHOP[page]
    caption = (
        f"<b>{pet['name']}</b>\n"
        f"Luck: {int(pet['luck'] * 100)}%\n"
        f"Price: <b>{pet['price']} coins</b>"
    )
    keyboard = [[
        InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev_{page}"),
        InlineKeyboardButton("Buy Now", callback_data=f"shop_buy_{page}"),
        InlineKeyboardButton("Next ➡️", callback_data=f"shop_next_{page}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=pet["img"], caption=caption, parse_mode="HTML"),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=pet["img"], caption=caption, parse_mode="HTML", reply_markup=reply_markup
        )

# /petshop command
async def petshop(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})
    if not user:
        await user_collection.insert_one({
            "id": user_id,
            "balance": 0,
            "pets": [DEFAULT_PET],
            "current_pet": DEFAULT_PET["name"]
        })
    await send_petshop_page(update, context, 0)

# Buy via /buypet
async def buypet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /buypet <pet_id> (e.g. /buypet 2)")
        return

    try:
        pet_id = int(context.args[0])
        pet = PET_SHOP[pet_id]
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid pet ID.")
        return

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "balance": 0,
            "pets": [DEFAULT_PET],
            "current_pet": DEFAULT_PET["name"]
        }
        await user_collection.insert_one(user)

    if any(p["name"] == pet["name"] for p in user.get("pets", [])):
        await update.message.reply_text(f"⚠️ You already own {pet['name']}.")
        return

    if user.get("balance", 0) < pet["price"]:
        await update.message.reply_text("❌ You don't have enough balance.")
        return

    await user_collection.update_one({"id": user_id}, {
        "$push": {"pets": pet},
        "$set": {"current_pet": pet["name"]},
        "$inc": {"balance": -pet["price"]}
    })

    await update.message.reply_photo(
        photo=pet["img"],
        caption=f"✅ You bought <b>{pet['name']}</b> with {int(pet['luck']*100)}% luck!",
        parse_mode="HTML"
    )

# /mypet command with pagination
async def send_mypet_page(update: Update, context: CallbackContext, page: int):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])

    if not pets:
        await update.message.reply_text("You have no pets. Use /petshop to buy one.")
        return

    page = page % len(pets)
    pet = pets[page]
    is_active = pet["name"] == current
    caption = (
        f"<b>Your Pet</b>\n"
        f"Name: <b>{pet['name']}</b>\n"
        f"Luck: {int(pet['luck'] * 100)}%\n"
        f"{'✅ This is your active pet.' if is_active else 'Click below to set as active.'}"
    )

    buttons = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data=f"mypet_prev_{page}"),
            InlineKeyboardButton("Set Active", callback_data=f"setpet_{page}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"mypet_next_{page}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    photo = pet.get("img", DEFAULT_PET["img"])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=photo, caption=caption, parse_mode="HTML", reply_markup=reply_markup
        )

# /mypet command
async def mypet(update: Update, context: CallbackContext):
    await send_mypet_page(update, context, 0)

# Set pet via button
async def setpet(update: Update, context: CallbackContext, index: int):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    if index >= len(pets):
        await update.callback_query.answer("Invalid pet index.", show_alert=True)
        return

    new_pet = pets[index]
    await user_collection.update_one({"id": user_id}, {"$set": {"current_pet": new_pet["name"]}})
    await update.callback_query.answer(f"✅ {new_pet['name']} is now your active pet.")
    await send_mypet_page(update, context, index)

# Callback button handler
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data.startswith("shop_next_") or data.startswith("shop_prev_"):
        page = int(data.split("_")[2])
        page = (page + 1) % len(PET_SHOP) if data.startswith("shop_next_") else (page - 1) % len(PET_SHOP)
        await send_petshop_page(update, context, page)

    elif data.startswith("shop_buy_"):
        page = int(data.split("_")[2])
        context.args = [str(page)]
        await buypet(update, context)

    elif data.startswith("mypet_next_") or data.startswith("mypet_prev_"):
        page = int(data.split("_")[2])
        user = await user_collection.find_one({"id": query.from_user.id})
        total = len(user.get("pets", [DEFAULT_PET]))
        page = (page + 1) % total if "next" in data else (page - 1) % total
        await send_mypet_page(update, context, page)

    elif data.startswith("setpet_"):
        index = int(data.split("_")[1])
        await setpet(update, context, index)

# Register all handlers
application.add_handler(CommandHandler("petshop", petshop))
application.add_handler(CommandHandler("buypet", buypet))
application.add_handler(CommandHandler("mypet", mypet))
application.add_handler(CallbackQueryHandler(button_handler))
        
