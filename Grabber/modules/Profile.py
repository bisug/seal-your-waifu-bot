from pyrogram import filters, types, enums
from Grabber import app, user_collection, PHOTO_URL, LOGGER
from Grabber.core.user import get_active_pet
from Grabber.core.progression import get_user_progress, get_progress_bar
import random

@app.on_message(filters.command(["myprofile", "profile", "me"]))
async def my_profile(_, message: types.Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        return await message.reply_text("🚨 <b>No profile found!</b> Try collecting a character first.", parse_mode=enums.ParseMode.HTML)

    user_name = message.from_user.first_name
    user_balance = user_data.get('balance', 0)
    characters_count = len(user_data.get('characters', []))
    
    # Progression Data
    progress = await get_user_progress(user_id)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"].capitalize()
    
    # Active Pet
    active_pet = await get_active_pet(user_id)
    pet_text = f"{active_pet['name']} (Lvl {active_pet.get('level', 1)})" if active_pet else "None"
    
    # Favorite Character
    fav_id = user_data.get('favorites', [None])[0]
    fav_char = next((c for c in user_data.get('characters', []) if str(c.get('id')) == str(fav_id)), None)
    fav_name = fav_char['name'] if fav_char else "None"

    # Profile Picture
    pic = random.choice(PHOTO_URL)

    # Visual Progress Bar
    pbar = get_progress_bar(xp_current, xp_needed, 10)

    profile_message = (
        f"<b>🌟 USER PROFILE 🌟</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"� <b>Name:</b> {user_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🎫 <b>Tier:</b> {pass_type}\n\n"
        f"⭐ <b>Level:</b> <code>{level}</code>\n"
        f"📊 <b>XP:</b> {pbar} <code>{xp_current}/{xp_needed}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Balance:</b> <code>{user_balance:,}</code> coins\n"
        f"🎒 <b>Characters:</b> <code>{characters_count}</code> collected\n"
        f"❤️ <b>Favorite:</b> <code>{fav_name}</code>\n"
        f"🐾 <b>Active Pet:</b> <code>{pet_text}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )

    buttons = [
        [types.InlineKeyboardButton("🎒 Harem", callback_data="harem_view"),
         types.InlineKeyboardButton("🎫 Pass", callback_data="pass_rewards")],
        [types.InlineKeyboardButton("🛒 Shop", callback_data="shop_next_0"),
         types.InlineKeyboardButton("🐾 Pets", callback_data="mypet_next_0")]
    ]

    try:
        await message.reply_photo(
            photo=pic, 
            caption=profile_message, 
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Profile Error: {e}")
        await message.reply_text(profile_message, parse_mode=enums.ParseMode.HTML)
