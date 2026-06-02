import time
from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, user_collection
from Grabber.core.cache import invalidate_user_cache, is_on_cooldown as redis_cooldown, sync_user_to_redis
from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from Grabber.core.user import add_pet_xp, get_user_filter
from Grabber.core.utils import html_escape, reply_media_dynamic
from Grabber.core.pets import (
    DEFAULT_PET,
    PET_SHOP,
    ensure_user_pet_state,
    find_pet_index,
    get_effective_affection,
    get_pet_key,
    normalize_pet,
    pet_for_storage,
    pet_matches,
)
async def send_petshop_page(message_or_query_obj, page: int, user_id: int):
    from Grabber.core.progression import get_user_progress
    pet = PET_SHOP[page]
    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)
    is_locked = user_level < req_level
    caption = (
        f"<b>{html_escape(pet['name'])}</b>\n"
        f"Ability: <b>{html_escape(pet.get('ability', 'None'))}</b>\n"
        f"<i>{html_escape(pet.get('desc', 'No ability'))}</i>\n"
        f"HP: {pet.get('hp', 100)} | ATK: {pet.get('atk', 10)} | SPD: {pet.get('spd', 10)}\n"
        f"Luck: {int(pet['luck'] * 100)}%\n"
        f"Price: <b>{pet['zenith_price']} ⬪</b>"
    )
    if is_locked:
        caption += f"\n\n<b>Requires Level {req_level}</b> (You: {user_level})"
    buy_button_text = f"Locked (Lvl {req_level})" if is_locked else "Buy Now"
    keyboard = [
        [
            types.InlineKeyboardButton("Prev", callback_data=f"shop_prev_{page}_{user_id}"),
            types.InlineKeyboardButton(buy_button_text, callback_data=f"shop_buy_{page}_{user_id}", style=enums.ButtonStyle.SUCCESS),
            types.InlineKeyboardButton("Next", callback_data=f"shop_next_{page}_{user_id}")
        ]
    ]
    is_private = False
    if isinstance(message_or_query_obj, types.CallbackQuery):
        is_private = message_or_query_obj.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query_obj.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#pets")
    if webapp_btn:
        keyboard.append([webapp_btn])
    keyboard.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])
    reply_markup = types.InlineKeyboardMarkup(keyboard)
    try:
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.edit_message_media(
                media=types.InputMediaPhoto(media=pet["img"], caption=caption),
                reply_markup=reply_markup
            )
        else:
            await reply_media_dynamic(message_or_query_obj, pet["img"], caption=caption, parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_petshop_page: {e}")
async def petshop_cmd(_, message: types.Message):
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#pets")
    builder = KeyboardBuilder()
    if webapp_btn:
        builder.add_row(webapp_btn)
    markup = builder.build()
    text = "<b>Open the Mini App to visit the Pet Shop!</b>"
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
async def perform_pet_purchase(user_id, pet_index: int):
    from Grabber.core.progression import get_user_progress
    try:
        if pet_index < 0:
            raise IndexError
        pet = normalize_pet(PET_SHOP[pet_index])
    except IndexError:
        return "Invalid pet selection."
    user_progress = await get_user_progress(user_id)
    user_level = user_progress["level"]
    req_level = pet.get("req_level", 0)
    if user_level < req_level:
        return f"You need to reach <b>Level {req_level}</b> to purchase this pet! (Current: {user_level})"
    user = await ensure_user_pet_state(user_id)
    # 1. Check Ownership BEFORE deduction
    if any(pet_matches(p, pet.get("id")) or pet_matches(p, pet.get("name")) for p in user.get("pets", [])):
        return f"You already own {pet['name']}."
    # 2. Check Balance
    user_zenith = user.get("zenith", 0)
    price = pet["zenith_price"]
    if user_zenith < price:
        return f"You need <b>{price} ⬪ Zenith</b> to purchase this pet! (You have: {user_zenith} ⬪)"
    # 3. Atomic Deduction and Push
    pet_id = get_pet_key(pet)
    pet_doc = pet_for_storage(pet)
    purchase_filter = get_user_filter(user_id)
    purchase_filter["zenith"] = {"$gte": price}
    purchase_filter["pets.id"] = {"$ne": pet_id}
    purchase_filter["pets.name"] = {"$ne": pet["name"]}
    update_result = await user_collection.update_one(
        purchase_filter,
        {
            "$inc": {"zenith": -price, "version": 1},
            "$push": {"pets": pet_doc},
            "$set": {"current_pet": pet_id}
        }
    )
    if update_result.modified_count == 0:
        return "Purchase failed. Your balance or pet ownership may have changed. Please try again."
    await sync_user_to_redis(user_id)
    return True
async def buypet_cmd(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: <code>/buypet &lt;pet_id&gt;</code>", parse_mode=enums.ParseMode.HTML)
    try:
        pet_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid pet ID.", parse_mode=enums.ParseMode.HTML)
    result = await perform_pet_purchase(message.from_user.id, pet_id)
    if result is True:
        pet = PET_SHOP[pet_id]
        await reply_media_dynamic(message, pet["img"],
            caption=f"You bought <b>{html_escape(pet['name'])}</b> with {int(pet['luck']*100)}% luck!",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(result, parse_mode=enums.ParseMode.HTML)
async def send_mypet_page(message_or_query_obj, page: int, user_id: int):
    user = await ensure_user_pet_state(user_id)
    pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
    current = user.get("current_pet")
    if not current and pets:
        current = get_pet_key(pets[0])
        await user_collection.update_one(get_user_filter(user_id), {"$set": {"current_pet": current}})
    if not pets:
        text = "You have no pets. Use /petshop to buy one."
        if isinstance(message_or_query_obj, types.CallbackQuery):
            await message_or_query_obj.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
        else:
            await message_or_query_obj.reply_text(text, parse_mode=enums.ParseMode.HTML)
        return
    page = page % len(pets)
    pet = pets[page]
    is_active = pet_matches(pet, current)
    level = pet.get("level", 1)
    xp = pet.get("xp", 0)
    needed = level * 100
    eff_affection = get_effective_affection(pet)
    if eff_affection >= 80:
        mood = "Happy"
    elif eff_affection <= 20:
        mood = "Sad"
    else:
        mood = "Neutral"
    caption = (
        f"<b>Your Pet</b>\n"
        f"Name: <b>{html_escape(pet['name'])}</b>\n"
        f"Ability: <b>{html_escape(pet.get('ability', 'None'))}</b>\n"
        f"Level: <code>{level}</code> | XP: <code>{xp}/{needed}</code>\n"
        f"Affection: <code>{eff_affection}/100</code> ({mood})\n"
        f"HP: <code>{pet.get('hp', 100)}</code> | ATK: <code>{pet.get('atk', 10)}</code> | SPD: <code>{pet.get('spd', 10)}</code>\n"
        f"Luck: <code>{int(pet['luck'] * 100)}%</code>\n\n"
        f"{'◉ <b>Active Pet</b>' if is_active else '◌ <i>Inactive</i>'}"
    )
    buttons = [
        [
            types.InlineKeyboardButton("«", callback_data=f"mypet_prev_{page}_{user_id}"),
            types.InlineKeyboardButton("Set Active" if not is_active else "Active", callback_data=f"setpet_{page}_{user_id}", style=enums.ButtonStyle.PRIMARY),
            types.InlineKeyboardButton("»", callback_data=f"mypet_next_{page}_{user_id}")
        ]
    ]
    is_private = False
    if isinstance(message_or_query_obj, types.CallbackQuery):
        is_private = message_or_query_obj.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query_obj.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#mypets")
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
            await reply_media_dynamic(message_or_query_obj, photo, caption=caption, parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_mypet_page: {e}")
async def mypet_cmd(_, message: types.Message):
    is_private = message.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#mypets")
    builder = KeyboardBuilder()
    if webapp_btn:
        builder.add_row(webapp_btn)
    markup = builder.build()
    text = "<b>Visit your Profile in the Mini App to manage your pets!</b>"
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
async def shop_mypet_navigation_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    action_type = data[0]
    action = data[1]
    page = int(data[2])
    owner_id = int(data[3])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)
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
            text = f"<b>Confirm Purchase</b>\n\nBuy <b>{html_escape(pet['name'])}</b> for <b>{pet['zenith_price']} ⬪</b>?"
            keyboard = [[
                types.InlineKeyboardButton("Confirm", callback_data=f"petconfirm_{page}_{owner_id}", style=enums.ButtonStyle.SUCCESS),
                types.InlineKeyboardButton("Cancel", callback_data=f"shop_view_{page}_{owner_id}", style=enums.ButtonStyle.DANGER)
            ]]
            await query.message.edit_caption(text, reply_markup=types.InlineKeyboardMarkup(keyboard))
            return
        await send_petshop_page(query, page, owner_id)
    elif action_type == "mypet":
        user_id = owner_id
        user = await ensure_user_pet_state(user_id)
        total = len(user.get("pets", [DEFAULT_PET]))
        if action == "next":
            page = (page + 1) % total
        else:
            page = (page - 1) % total
        await send_mypet_page(query, page, user_id)
async def pet_confirm_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    page = int(data[1])
    owner_id = int(data[2])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)
    result = await perform_pet_purchase(owner_id, page)
    if result is True:
        await query.answer(f"Success! You bought {PET_SHOP[page]['name']}.", show_alert=True)
        await send_mypet_page(query, 0, owner_id)
    else:
        await query.answer(str(result), show_alert=True)
        await send_petshop_page(query, page, owner_id)
async def setpet_callback(_, query: types.CallbackQuery):
    data = query.data.split("_")
    index = int(data[1])
    owner_id = int(data[2])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your menu!", show_alert=True)
    user_id = owner_id
    user = await ensure_user_pet_state(user_id)
    pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
    if index >= len(pets):
        await query.answer("Invalid pet index.", show_alert=True)
        return
    new_pet = pets[index]
    await user_collection.update_one(get_user_filter(user_id), {"$set": {"current_pet": get_pet_key(new_pet)}})
    await invalidate_user_cache(user_id)
    await query.answer(f"{new_pet['name']} is now your active pet.")
    await send_mypet_page(query, index, user_id)
async def feed_pet_cmd(_, message: types.Message):
    user_id = message.from_user.id
    on_cd, secs = await redis_cooldown("feed_pet", user_id, 900) # 15 minutes
    if on_cd:
        return await message.reply_text(f"🍱 <b>Your pet is full!</b>\nTry feeding again in <b>{int(secs/60)}m {secs%60}s</b>.", parse_mode=enums.ParseMode.HTML)
    user = await ensure_user_pet_state(user_id)
    pets = [normalize_pet(p) for p in user.get("pets", [])]
    active_pet_name = user.get("current_pet")
    pet_index = find_pet_index(pets, active_pet_name)
    if pet_index == -1:
        pet_list_str = ", ".join([p["name"] for p in pets])
        return await message.reply_text(f"❌ <b>Active Pet Error:</b> '{active_pet_name}' not found.\nAvailable: {pet_list_str}")
    pet = pets[pet_index]
    pet_name = pet["name"]
    current_affection = get_effective_affection(pet)
    new_affection = min(100, current_affection + 15)
    await user_collection.update_one(
        get_user_filter(user_id),
        {"$set": {
            f"pets.{pet_index}.affection": new_affection,
            f"pets.{pet_index}.last_interacted": time.time()
        }}
    )
    await invalidate_user_cache(user_id)
    caption = (
        f"🍱 <b>Meal Time!</b>\n\n"
        f"You fed <b>{pet_name}</b> with some delicious snacks!\n"
        f"Affection: <code>{current_affection}</code> ➜ <b>{new_affection}/100</b> ❤️"
    )
    await message.reply_text(caption, parse_mode=enums.ParseMode.HTML)
async def train_pet_cmd(_, message: types.Message):
    user_id = message.from_user.id
    on_cd, secs = await redis_cooldown("train_pet", user_id, 1800) # 30 minutes
    if on_cd:
        return await message.reply_text(f"⚔️ <b>Your pet is tired!</b>\nTry training again in <b>{int(secs/60)}m {secs%60}s</b>.", parse_mode=enums.ParseMode.HTML)
    user = await ensure_user_pet_state(user_id)
    pets = [normalize_pet(p) for p in user.get("pets", [])]
    active_pet_name = user.get("current_pet")
    pet_index = find_pet_index(pets, active_pet_name)
    if pet_index == -1:
        pet_list_str = ", ".join([p["name"] for p in pets])
        return await message.reply_text(f"❌ <b>Active Pet Error:</b> '{active_pet_name}' not found.\nAvailable: {pet_list_str}")
    pet = pets[pet_index]
    pet_name = pet["name"]
    current_affection = get_effective_affection(pet)
    new_affection = min(100, current_affection + 10)
    # Update affection
    await user_collection.update_one(
        get_user_filter(user_id),
        {"$set": {
            f"pets.{pet_index}.affection": new_affection,
            f"pets.{pet_index}.last_interacted": time.time()
        }}
    )
    await invalidate_user_cache(user_id)
    # Add XP
    await add_pet_xp(user_id, get_pet_key(pet), 5)
    caption = (
        f"⚔️ <b>Training Session!</b>\n\n"
        f"<b>{pet_name}</b> worked hard and improved its skills!\n"
        f"Affection: <b>{new_affection}/100</b> ❤️\n"
        f"XP Gained: <b>+5</b> ✨"
    )
    await message.reply_text(caption, parse_mode=enums.ParseMode.HTML)
def load_handlers(bot):
    """Explicitly register pet handlers. Resolves multi-bot ghosting."""
    if bot.name != "MainBot":
        return
    # Commands
    bot.add_handler(MessageHandler(petshop_cmd, filters.command("petshop")), group=0)
    bot.add_handler(MessageHandler(buypet_cmd, filters.command("buypet")), group=0)
    bot.add_handler(MessageHandler(mypet_cmd, filters.command(["mypet", "pet", "pets"])), group=0)
    bot.add_handler(MessageHandler(feed_pet_cmd, filters.command("feed")), group=0)
    bot.add_handler(MessageHandler(train_pet_cmd, filters.command("train")), group=0)
    # Callback Queries
    bot.add_handler(CallbackQueryHandler(shop_mypet_navigation_callback, filters.regex(r"^(shop|mypet)_(next|prev|view|buy)_(\d+)_(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(pet_confirm_callback, filters.regex(r"^petconfirm_(\d+)_(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(setpet_callback, filters.regex(r"^setpet_(\d+)_(\d+)$")), group=0)
    LOGGER.info(f"Registered Pet System handlers for {bot.name}")
