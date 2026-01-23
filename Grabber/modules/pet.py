from pyrogram import filters, types, enums, errors
from Grabber import app, user_collection, PHOTO_URL, LOGGER

# Default Pet
DEFAULT_PET = {
    "name": "Fluffy Fox 🦊",
    "luck": 0.10,
    "level": 1,
    "xp": 0,
    "owned": True,
    "img": PHOTO_URL[0]
}

# Pet Shop List
PET_SHOP = [
    {"name": "Blaze Fang 🐺", "luck": 0.15, "level": 1, "xp": 0, "price": 10000, "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg"},
    {"name": "Mystic Dragon 🐲", "luck": 0.25, "level": 1, "xp": 0, "price": 25000, "img": "https://files.catbox.moe/7kvcqj.jpg"},
    {"name": "Shadow Panther 🐆", "luck": 0.35, "level": 1, "xp": 0, "price": 50000, "img": "https://i.ibb.co/8CdC5QG/file-86.jpg"},
    {"name": "Cosmic Phoenix 🦅", "luck": 0.50, "level": 1, "xp": 0, "price": 100000, "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg"},
]

# Send Pet Shop Page
async def send_petshop_page(message_or_query_obj, page: int):
    pet = PET_SHOP[page]
    caption = (
        f"**{pet['name']}**\n"
        f"Luck: {int(pet['luck'] * 100)}%\n"
        f"Price: **{pet['price']} coins**"
    )
    keyboard = [[
        types.InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev_{page}"),
        types.InlineKeyboardButton("Buy Now", callback_data=f"shop_buy_{page}"),
        types.InlineKeyboardButton("Next ➡️", callback_data=f"shop_next_{page}")
    ]]
    reply_markup = types.InlineKeyboardMarkup(keyboard)

    try:
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.message.edit_media(
                media=types.InputMediaPhoto(media=pet["img"], caption=caption, parse_mode=enums.ParseMode.MARKDOWN),
                reply_markup=reply_markup
            )
        else:
            await message_or_query_obj.reply_photo(
                photo=pet["img"], caption=caption, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_petshop_page: {e}")

# /petshop command
@app.on_message(filters.command("petshop"))
async def petshop(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    if not user:
        await user_collection.insert_one({
            "id": user_id,
            "balance": 0,
            "pets": [DEFAULT_PET],
            "current_pet": DEFAULT_PET["name"]
        })
    await send_petshop_page(message, 0)

# Buy via /buypet
@app.on_message(filters.command("buypet"))
async def buypet_cmd(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: <code>/buypet &lt;pet_id&gt;</code>", parse_mode=enums.ParseMode.HTML)
    
    try:
        pet_id = int(message.command[1])
        pet = PET_SHOP[pet_id]
    except (ValueError, IndexError):
        await message.reply_text("❌ Invalid pet ID.")
        return

    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {"id": user_id, "balance": 0, "pets": [DEFAULT_PET], "current_pet": DEFAULT_PET["name"]}
        await user_collection.insert_one(user)

    if any(p["name"] == pet["name"] for p in user.get("pets", [])):
        await message.reply_text(f"⚠️ You already own {pet['name']}.")
        return

    if user.get("balance", 0) < pet["price"]:
        await message.reply_text("❌ You don't have enough balance.")
        return

    await user_collection.update_one({"id": user_id}, {
        "$push": {"pets": pet},
        "$set": {"current_pet": pet["name"]},
        "$inc": {"balance": -pet["price"]}
    })

    await message.reply_photo(
        photo=pet["img"],
        caption=f"✅ You bought **{pet['name']}** with {int(pet['luck']*100)}% luck!",
        parse_mode=enums.ParseMode.MARKDOWN
    )

# /mypet command with pagination
async def send_mypet_page(message_or_query_obj, page: int, user_id: int):
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])

    if not pets:
        text = "You have no pets. Use /petshop to buy one."
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.message.edit_text(text)
        else:
            await message_or_query_obj.reply_text(text)
        return

    page = page % len(pets)
    pet = pets[page]
    is_active = pet["name"] == current
    
    level = pet.get("level", 1)
    xp = pet.get("xp", 0)
    needed = level * 100
    
    caption = (
        f"🐾 **Your Pet**\n"
        f"Name: **{pet['name']}**\n"
        f"Level: `{level}`\n"
        f"XP: `{xp}/{needed}`\n"
        f"Luck: `{int(pet['luck'] * 100)}%`\n\n"
        f"{'✅ **Active Pet**' if is_active else '⚠️ *Inactive*'}"
    )

    buttons = [
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"mypet_prev_{page}"),
            types.InlineKeyboardButton("Set Active" if not is_active else "🌟 Active", callback_data=f"setpet_{page}"),
            types.InlineKeyboardButton("Next ➡️", callback_data=f"mypet_next_{page}")
        ]
    ]
    reply_markup = types.InlineKeyboardMarkup(buttons)
    photo = pet.get("img", DEFAULT_PET["img"])

    try:
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.message.edit_media(
                media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode=enums.ParseMode.MARKDOWN),
                reply_markup=reply_markup
            )
        else:
            await message_or_query_obj.reply_photo(
                photo=photo, caption=caption, parse_mode=enums.ParseMode.MARKDOWN, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_mypet_page: {e}")

# /mypet command
@app.on_message(filters.command("mypet"))
async def mypet_cmd(_, message: types.Message):
    await send_mypet_page(message, 0, message.from_user.id)

@app.on_callback_query(filters.regex(r"^(shop|mypet)_(next|prev|buy)_(\d+)$"))
async def shop_mypet_navigation(_, query: types.CallbackQuery):
    data = query.data
    page = int(data.split("_")[2])
    
    if data.startswith("shop_"):
        if "next" in data:
            page = (page + 1) % len(PET_SHOP)
        elif "prev" in data:
            page = (page - 1) % len(PET_SHOP)
        elif "buy" in data:
            await send_petshop_page(query, page)
            return

        await send_petshop_page(query, page)
    
    elif data.startswith("mypet_"):
        user_id = query.from_user.id
        user = await user_collection.find_one({"id": user_id})
        total = len(user.get("pets", [DEFAULT_PET]))
        if "next" in data:
            page = (page + 1) % total
        else:
            page = (page - 1) % total
        await send_mypet_page(query, page, user_id)
    
    await query.answer()

@app.on_callback_query(filters.regex(r"^setpet_(\d+)$"))
async def setpet_callback(_, query: types.CallbackQuery):
    index = int(query.data.split("_")[1])
    user_id = query.from_user.id
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    
    if index >= len(pets):
        await query.answer("Invalid pet index.", show_alert=True)
        return

    new_pet = pets[index]
    await user_collection.update_one({"id": user_id}, {"$set": {"current_pet": new_pet["name"]}})
    await query.answer(f"✅ {new_pet['name']} is now your active pet.")
    await send_mypet_page(query, index, user_id)
