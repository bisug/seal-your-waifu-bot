import time

from pyrogram import enums, errors, filters, types
from pyrogram.enums import ButtonStyle, ParseMode

from config import config
from Grabber import LOGGER, PHOTO_URL, WEB_APP_URL, app, user_collection
from Grabber.core.cache import is_on_cooldown as redis_cooldown
from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
from Grabber.core.user import add_pet_xp
from Grabber.core.utils import html_escape, reply_media_dynamic

DEFAULT_PET = {
    "name": "Fluffy Fox 🦊",
    "luck": 0.10,
    "hp": 195,
    "atk": 38,
    "spd": 29,
    "level": 10,
    "xp": 0,
    "owned": True,
    "ability": "Beginner's Luck",
    "desc": "+5% XP Gain",
    "img": PHOTO_URL[0],
    "affection": 50,
    "last_interacted": 0
}


PET_SHOP = [
    {"name": "Blaze Fang 🐺", "luck": 0.15, "hp": 180, "atk": 30, "spd": 15, "level": 1, "xp": 0, "zenith_price": 2, "req_level": 0, "ability": "Scavenger", "desc": "20% Chance for Double Shards", "img": "https://i.ibb.co/fd1qPVJs/file-89.jpg", "affection": 50, "last_interacted": 0},
    {"name": "Shadow Panther 🐆", "luck": 0.25, "hp": 140, "atk": 40, "spd": 35, "level": 1, "xp": 0, "zenith_price": 5, "req_level": 10, "ability": "Speedster", "desc": "-10s Hunt Cooldown", "img": "https://i.ibb.co/8CdC5QG/file-86.jpg", "affection": 50, "last_interacted": 0},
    {"name": "Cosmic Phoenix 🦅", "luck": 0.35, "hp": 220, "atk": 25, "spd": 25, "level": 1, "xp": 0, "zenith_price": 12, "req_level": 15, "ability": "Caregiver", "desc": "50% Faster Egg Hatching", "img": "https://i.ibb.co/b5CrL8rp/file-84.jpg", "affection": 50, "last_interacted": 0},
    {"name": "Mystic Dragon 🐲", "luck": 0.50, "hp": 300, "atk": 45, "spd": 10, "level": 1, "xp": 0, "zenith_price": 25, "req_level": 20, "ability": "Hoarder", "desc": "5% Chance for Bonus Egg", "img": "https://files.catbox.moe/7kvcqj.jpg", "affection": 50, "last_interacted": 0},
]


async def send_petshop_page(message_or_query_obj, page: int, user_id: int):
    from Grabber.core.progression import get_user_progress

    pet = PET_SHOP[page]
    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)
    is_locked = user_level < req_level

    caption = (
        f"<b>{html_escape(pet['name'])}</b>\n"
        f"✨ Ability: <b>{html_escape(pet.get('ability', 'None'))}</b>\n"
        f"📖 <i>{html_escape(pet.get('desc', 'No ability'))}</i>\n"
        f"❤️ HP: {pet.get('hp', 100)} | ⚔️ ATK: {pet.get('atk', 10)} | ⚡ SPD: {pet.get('spd', 10)}\n"
        f"🍀 Luck: {int(pet['luck'] * 100)}%\n"
        f"💰 Price: <b>{pet['zenith_price']} ⧫</b>"
    )

    if is_locked:
        caption += f"\n\n🔒 <b>Requires Level {req_level}</b> (You: {user_level})"


    buy_button_text = f"🔒 Locked (Lvl {req_level})" if is_locked else "Buy Now"
    keyboard = [
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev_{page}_{user_id}"),
            types.InlineKeyboardButton(buy_button_text, callback_data=f"shop_buy_{page}_{user_id}", style=enums.ButtonStyle.SUCCESS),
            types.InlineKeyboardButton("Next ➡️", callback_data=f"shop_next_{page}_{user_id}")
        ]
    ]

    is_private = False
    if isinstance(message_or_query_obj, types.CallbackQuery):
        is_private = message_or_query_obj.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query_obj.chat.type == enums.ChatType.PRIVATE
        
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        keyboard.append([webapp_btn])
        
    keyboard.append([types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")])
    reply_markup = types.InlineKeyboardMarkup(keyboard)

    try:
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.edit_message_media(
                media=types.InputMediaPhoto(media=pet["img"], caption=caption),
                reply_markup=reply_markup
            )
        else:
            await reply_media_dynamic(message_or_query_obj, pet["img"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_petshop_page: {e}")


@app.on_message(filters.command("petshop"))
async def petshop(_, message: types.Message):
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#shop")
    builder = KeyboardBuilder()
    if webapp_btn:
        builder.add_row(webapp_btn)
    
    markup = builder.build()
    text = "🐾 <b>Open the Mini App to visit the Pet Shop!</b>"
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def perform_pet_purchase(user_id, pet_index: int):
    from Grabber.core.progression import get_user_progress

    try:
        pet = PET_SHOP[pet_index]
    except IndexError:
        return "❌ Invalid pet selection."


    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)

    if user_level < req_level:
        return f"🔒 You need to reach <b>Level {req_level}</b> to purchase this pet! (Current: {user_level})"

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {"id": user_id, "balance": 0, "zenith": 0, "pets": [DEFAULT_PET.copy()], "current_pet": DEFAULT_PET["name"]}
        await user_collection.insert_one(user)

    # 1. Check Ownership BEFORE deduction
    if any(p["name"] == pet["name"] for p in user.get("pets", [])):
        return f"⚠️ You already own {pet['name']}."

    # 2. Check Balance
    user_zenith = user.get("zenith", 0)
    price = pet["zenith_price"]

    if user_zenith < price:
        return f"❌ You need <b>{price} ⧫ Zenith</b> to purchase this pet! (You have: {user_zenith} ⧫)"

    # 3. Atomic Deduction and Push
    update_result = await user_collection.update_one(
        {"id": user_id, "zenith": {"$gte": price}},
        {
            "$inc": {"zenith": -price},
            "$push": {"pets": pet},
            "$set": {"current_pet": pet["name"]}
        }
    )

    if update_result.modified_count == 0:
        return "❌ Purchase failed. Your balance may have changed. Please try again."

    return True



@app.on_message(filters.command("buypet"))
async def buypet_cmd(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: <code>/buypet &lt;pet_id&gt;</code>", parse_mode=ParseMode.HTML)

    try:
        pet_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Invalid pet ID.", parse_mode=ParseMode.HTML)

    result = await perform_pet_purchase(message.from_user.id, pet_id)
    if result is True:
        pet = PET_SHOP[pet_id]
        await reply_media_dynamic(message, pet["img"],
            caption=f"✅ You bought <b>{html_escape(pet['name'])}</b> with {int(pet['luck']*100)}% luck!",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(result, parse_mode=ParseMode.HTML)


def get_effective_affection(pet: dict) -> int:
    base_affection = pet.get("affection", 50)
    last_interacted = pet.get("last_interacted", 0)
    
    if last_interacted == 0:
        return base_affection
        
    days_passed = (time.time() - last_interacted) / 86400.0
    decay = int(days_passed * 5)
    
    effective_affection = max(0, base_affection - decay)
    return effective_affection

async def send_mypet_page(message_or_query_obj, page: int, user_id: int):
    user = await user_collection.find_one({"id": user_id})
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])

    if not pets:
        text = "You have no pets. Use /petshop to buy one."
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.message.edit_text(text, parse_mode=ParseMode.HTML)
        else:
            await message_or_query_obj.reply_text(text, parse_mode=ParseMode.HTML)
        return

    page = page % len(pets)
    pet = pets[page]
    is_active = pet["name"] == current

    level = pet.get("level", 1)
    xp = pet.get("xp", 0)
    needed = level * 100

    eff_affection = get_effective_affection(pet)
    if eff_affection >= 80:
        mood = "🥰 Happy"
    elif eff_affection <= 20:
        mood = "😢 Sad"
    else:
        mood = "😐 Neutral"

    caption = (
        f"🐾 <b>Your Pet</b>\n"
        f"📛 Name: <b>{html_escape(pet['name'])}</b>\n"
        f"⚡ Ability: <b>{html_escape(pet.get('ability', 'None'))}</b>\n"
        f"📊 Level: <code>{level}</code> | XP: <code>{xp}/{needed}</code>\n"
        f"💖 Affection: <code>{eff_affection}/100</code> ({mood})\n"
        f"❤️ HP: <code>{pet.get('hp', 100)}</code> | ⚔️ ATK: <code>{pet.get('atk', 10)}</code> | ⚡ SPD: <code>{pet.get('spd', 10)}</code>\n"
        f"🍀 Luck: <code>{int(pet['luck'] * 100)}%</code>\n\n"
        f"{'✅ <b>Active Pet</b>' if is_active else '⚠️ <i>Inactive</i>'}"
    )

    buttons = [
        [
            types.InlineKeyboardButton("⬅️", callback_data=f"mypet_prev_{page}_{user_id}"),
            types.InlineKeyboardButton("Set Active" if not is_active else "Active", callback_data=f"setpet_{page}_{user_id}", style=enums.ButtonStyle.PRIMARY),
            types.InlineKeyboardButton("➡️", callback_data=f"mypet_next_{page}_{user_id}")
        ]
    ]

    is_private = False
    if isinstance(message_or_query_obj, types.CallbackQuery):
        is_private = message_or_query_obj.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query_obj.chat.type == enums.ChatType.PRIVATE
        
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        buttons.append([webapp_btn])

    buttons.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])
    reply_markup = types.InlineKeyboardMarkup(buttons)
    photo = pet.get("img", DEFAULT_PET["img"])

    try:
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.edit_message_media(
                media=types.InputMediaPhoto(media=photo, caption=caption),
                reply_markup=reply_markup
            )
        else:
            await reply_media_dynamic(message_or_query_obj, photo, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_mypet_page: {e}")


@app.on_message(filters.command(["mypet", "pet", "pets"]))
async def mypet_cmd(_, message: types.Message):
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private)
    builder = KeyboardBuilder()
    if webapp_btn:
        builder.add_row(webapp_btn)
    
    markup = builder.build()
    text = "🐾 <b>Visit your Profile in the Mini App to manage your pets!</b>"
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^(shop|mypet)_(next|prev|view|buy)_(\d+)_(\d+)$"))
async def shop_mypet_navigation(_, query: types.CallbackQuery):
    data = query.data.split("_")
    action_type = data[0]
    action = data[1]
    page = int(data[2])
    owner_id = int(data[3])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your menu!", show_alert=True)

    await query.answer()  # Dismiss spinner instantly

    if action_type == "shop":
        if action == "next":
            page = (page + 1) % len(PET_SHOP)
        elif action == "prev":
            page = (page - 1) % len(PET_SHOP)
        elif action == "view":
            pass  # Keep exactly the same page
        elif action == "buy":
            pet = PET_SHOP[page]
            text = f"⚠️ <b>Confirm Purchase</b>\n\nBuy <b>{html_escape(pet['name'])}</b> for <b>{pet['zenith_price']} ⧫</b>?"
            keyboard = [[
                types.InlineKeyboardButton("Confirm ✅", callback_data=f"petconfirm_{page}_{owner_id}", style=enums.ButtonStyle.SUCCESS),
                types.InlineKeyboardButton("Cancel ❌", callback_data=f"shop_view_{page}_{owner_id}", style=enums.ButtonStyle.DANGER)
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

@app.on_message(filters.command("feed"))
async def feed_pet_cmd(_, message: types.Message):
    user_id = message.from_user.id
    
    on_cd, secs = await redis_cooldown("feed_pet", user_id, 14400) # 4 hours
    if on_cd:
        return await message.reply_text(f"⏳ Your pet is full! Try again in <b>{int(secs/60)}m {secs%60}s</b>.", parse_mode=ParseMode.HTML)
        
    user = await user_collection.find_one({"id": user_id})
    if not user or "current_pet" not in user:
        return await message.reply_text("❌ You don't have an active pet to feed.")
        
    active_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    pet_index = next((i for i, p in enumerate(pets) if p["name"] == active_pet_name), -1)
    
    if pet_index == -1:
        return await message.reply_text("❌ Active pet not found.")
        
    pet = pets[pet_index]
    current_affection = get_effective_affection(pet)
    new_affection = min(100, current_affection + 15)
    
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {
            f"pets.{pet_index}.affection": new_affection,
            f"pets.{pet_index}.last_interacted": time.time()
        }}
    )
    
    await message.reply_text(f"🍲 You fed <b>{active_pet_name}</b>!\n💖 Affection increased to <b>{new_affection}/100</b>.", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("train"))
async def train_pet_cmd(_, message: types.Message):
    user_id = message.from_user.id
    
    on_cd, secs = await redis_cooldown("train_pet", user_id, 7200) # 2 hours
    if on_cd:
        return await message.reply_text(f"⏳ Your pet is tired! Try training again in <b>{int(secs/60)}m {secs%60}s</b>.", parse_mode=ParseMode.HTML)
        
    user = await user_collection.find_one({"id": user_id})
    if not user or "current_pet" not in user:
        return await message.reply_text("❌ You don't have an active pet to train.")
        
    active_pet_name = user["current_pet"]
    pets = user.get("pets", [])
    pet_index = next((i for i, p in enumerate(pets) if p["name"] == active_pet_name), -1)
    
    if pet_index == -1:
        return await message.reply_text("❌ Active pet not found.")
        
    pet = pets[pet_index]
    current_affection = get_effective_affection(pet)
    new_affection = min(100, current_affection + 10)
    
    # Update affection
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {
            f"pets.{pet_index}.affection": new_affection,
            f"pets.{pet_index}.last_interacted": time.time()
        }}
    )
    
    # Add XP
    await add_pet_xp(user_id, active_pet_name, 5)
    
    await message.reply_text(f"⚔️ You trained <b>{active_pet_name}</b>!\n💖 Affection increased to <b>{new_affection}/100</b>.\n🆙 Gained <b>+5 XP</b>.", parse_mode=ParseMode.HTML)
