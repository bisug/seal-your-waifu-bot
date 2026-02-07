from pyrogram import filters, types, enums, errors
from Grabber import app, user_collection, PHOTO_URL, LOGGER

# Default Pet
DEFAULT_PET = {
    "name": "Fluffy Fox 🦊",
    "luck": 0.10,
    "hp": 195,  # 150 + 45 (Level 10 bonus)
    "atk": 38,  # 20 + 18
    "spd": 29,  # 20 + 9
    "level": 10,
    "xp": 0,
    "owned": True,
    "ability": "Beginner's Luck",
    "desc": "+5% XP Gain",
    "img": PHOTO_URL[0]
}

# Pet Shop List
PET_SHOP = [
    {"name": "Blaze Fang 🐺", "luck": 0.15, "hp": 180, "atk": 30, "spd": 15, "level": 1, "xp": 0, "zenith_price": 2, "req_level": 0, "ability": "Scavenger", "desc": "20% Chance for Double Coins", "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg"},
    {"name": "Shadow Panther 🐆", "luck": 0.25, "hp": 140, "atk": 40, "spd": 35, "level": 1, "xp": 0, "zenith_price": 5, "req_level": 10, "ability": "Speedster", "desc": "-10s Hunt Cooldown", "img": "https://i.ibb.co/8CdC5QG/file-86.jpg"},
    {"name": "Cosmic Phoenix 🦅", "luck": 0.35, "hp": 220, "atk": 25, "spd": 25, "level": 1, "xp": 0, "zenith_price": 12, "req_level": 15, "ability": "Caregiver", "desc": "50% Faster Egg Hatching", "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg"},
    {"name": "Mystic Dragon 🐲", "luck": 0.50, "hp": 300, "atk": 45, "spd": 10, "level": 1, "xp": 0, "zenith_price": 25, "req_level": 20, "ability": "Hoarder", "desc": "5% Chance for Bonus Egg", "img": "https://files.catbox.moe/7kvcqj.jpg"},
]

# Send Pet Shop Page
async def send_petshop_page(message_or_query_obj, page: int, user_id: int):
    from Grabber.core.progression import get_user_progress
    
    pet = PET_SHOP[page]
    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)
    is_locked = user_level < req_level
    
    caption = (
        f"**{pet['name']}**\n"
        f"✨ Ability: **{pet.get('ability', 'None')}**\n"
        f"📖 _{pet.get('desc', 'No ability')}_\n"
        f"❤️ HP: {pet.get('hp', 100)} | ⚔️ ATK: {pet.get('atk', 10)} | ⚡ SPD: {pet.get('spd', 10)}\n"
        f"🍀 Luck: {int(pet['luck'] * 100)}%\n"
        f"💰 Price: **{pet['zenith_price']} ⧫**"
    )
    
    if is_locked:
        caption += f"\n\n🔒 **Requires Level {req_level}** (You: {user_level})"
    
    # Button text based on lock status
    buy_button_text = f"🔒 Locked (Lvl {req_level})" if is_locked else "Buy Now"
    keyboard = [
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev_{page}_{user_id}"),
            types.InlineKeyboardButton(buy_button_text, callback_data=f"shop_buy_{page}_{user_id}"),
            types.InlineKeyboardButton("Next ➡️", callback_data=f"shop_next_{page}_{user_id}")
        ],
        [types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")]
    ]
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
    await send_petshop_page(message, 0, user_id)

# Purchase Logic Helper
async def perform_pet_purchase(user_id, pet_index: int):
    from Grabber.core.progression import get_user_progress
    
    try:
        pet = PET_SHOP[pet_index]
    except IndexError:
        return "❌ Invalid pet selection."
    
    # Check level requirement
    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)
    
    if user_level < req_level:
        return f"🔒 You need to reach **Level {req_level}** to purchase this pet! (Current: {user_level})"

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {"id": user_id, "balance": 0, "zenith": 0, "pets": [DEFAULT_PET.copy()], "current_pet": DEFAULT_PET["name"]}
        await user_collection.insert_one(user)
    
    user_zenith = user.get("zenith", 0)
    price = pet["zenith_price"]
    
    if user_zenith < price:
        return f"❌ You need **{price} ⧫ Zenith** to purchase this pet! (You have: {user_zenith} ⧫)"
    
    # Deduct Zenith
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"zenith": -price}}
    )

    if any(p["name"] == pet["name"] for p in user.get("pets", [])):
        return f"⚠️ You already own {pet['name']}."

    await user_collection.update_one({"id": user_id}, {
        "$push": {"pets": pet},
        "$set": {"current_pet": pet["name"]}
    })
    return True

# Buy via /buypet
@app.on_message(filters.command("buypet"))
async def buypet_cmd(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/buypet <pet_id>`", parse_mode=enums.ParseMode.MARKDOWN)
    
    try:
        pet_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Invalid pet ID.")

    result = await perform_pet_purchase(message.from_user.id, pet_id)
    if result is True:
        pet = PET_SHOP[pet_id]
        await message.reply_photo(
            photo=pet["img"],
            caption=f"✅ You bought **{pet['name']}** with {int(pet['luck']*100)}% luck!",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(result)

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
        f"📛 Name: **{pet['name']}**\n"
        f"⚡ Ability: **{pet.get('ability', 'None')}**\n"
        f"📊 Level: `{level}` | XP: `{xp}/{needed}`\n"
        f"❤️ HP: `{pet.get('hp', 100)}` | ⚔️ ATK: `{pet.get('atk', 10)}` | ⚡ SPD: `{pet.get('spd', 10)}`\n"
        f"🍀 Luck: `{int(pet['luck'] * 100)}%`\n\n"
        f"{'✅ **Active Pet**' if is_active else '⚠️ _Inactive_'}"
    )

    buttons = [
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"mypet_prev_{page}_{user_id}"),
            types.InlineKeyboardButton("Set Active" if not is_active else "🌟 Active", callback_data=f"setpet_{page}_{user_id}"),
            types.InlineKeyboardButton("Next ➡️", callback_data=f"mypet_next_{page}_{user_id}")
        ],
        [types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")]
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
@app.on_message(filters.command(["mypet", "pet", "pets"]))
async def mypet_cmd(_, message: types.Message):
    await send_mypet_page(message, 0, message.from_user.id)

@app.on_callback_query(filters.regex(r"^(shop|mypet)_(next|prev|buy)_(\d+)_(\d+)$"))
async def shop_mypet_navigation(_, query: types.CallbackQuery):
    data = query.data.split("_")
    action_type = data[0] # shop or mypet
    action = data[1] # next/prev/buy
    page = int(data[2])
    owner_id = int(data[3])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)
    
    if action_type == "shop":
        if action == "next":
            page = (page + 1) % len(PET_SHOP)
        elif action == "prev":
            page = (page - 1) % len(PET_SHOP)
        elif action == "buy":
            pet = PET_SHOP[page]
            text = f"⚠️ **Confirm Purchase**\n\nBuy **{pet['name']}** for **{pet['price']} coins**?"
            keyboard = [[
                types.InlineKeyboardButton("Confirm ✅", callback_data=f"petconfirm_{page}_{owner_id}"),
                types.InlineKeyboardButton("Cancel ❌", callback_data=f"shop_next_{page}_{owner_id}")
            ]]
            await query.message.edit_caption(text, reply_markup=types.InlineKeyboardMarkup(keyboard))
            return
 
        await send_petshop_page(query, page, owner_id)
    
    elif action_type == "mypet":
        user_id = owner_id
        user = await user_collection.find_one({"id": user_id})
        total = len(user.get("pets", [DEFAULT_PET]))
        if action == "next":
            page = (page + 1) % total
        else:
            page = (page - 1) % total
        await send_mypet_page(query, page, user_id)
    
    await query.answer()

@app.on_callback_query(filters.regex(r"^petconfirm_(\d+)_(\d+)$"))
async def pet_confirm_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    page = int(data[1])
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    result = await perform_pet_purchase(owner_id, page)
    if result is True:
        await query.answer(f"✅ Success! You bought {PET_SHOP[page]['name']}.", show_alert=True)
        await send_mypet_page(query, 0, owner_id)
    else:
        await query.answer(str(result), show_alert=True)
        await send_petshop_page(query, page, owner_id)

@app.on_callback_query(filters.regex(r"^setpet_(\d+)_(\d+)$"))
async def setpet_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    index = int(data[1])
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)
    
    user_id = owner_id
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    
    if index >= len(pets):
        await query.answer("Invalid pet index.", show_alert=True)
        return

    new_pet = pets[index]
    await user_collection.update_one({"id": user_id}, {"$set": {"current_pet": new_pet["name"]}})
    await query.answer(f"✅ {new_pet['name']} is now your active pet.")
    await send_mypet_page(query, index, user_id)
