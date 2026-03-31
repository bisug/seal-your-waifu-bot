from Grabber.core.utils import reply_media_dynamic
import math
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, user_collection, PHOTO_URL, LOGGER, WEB_APP_URL
from config import config
from Grabber.core.utils import html_escape
from Grabber.core.user import get_user_data, get_active_pet
from Grabber.core.progression import get_user_progress, get_progress_bar
from Grabber.database import collection
import random

RARITY_ICONS = {
    '⚪ Common': '⚪', '🟢 Medium': '🟢', '🟠 Rare': '🟠',
    '🟡 Legendary': '🟡', '💠 Cosmic': '💠', '💮 Exclusive': '💮',
    '🔮 Limited Edition': '🔮'
}

@app.on_message(filters.command(["profile", "myprofile", "me", "status", "mystatus"]))
async def profile_handler(_, message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        return await message.reply_text("🚨 <b>No profile found!</b> Try collecting a character first.", parse_mode=ParseMode.HTML)

    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)


    user_name = html_escape(message.from_user.first_name)
    user_balance = user_data.get('balance', 0)
    zenith = user_data.get('zenith', 0)


    chars = user_data.get('characters', [])
    char_count = len(chars)
    total_db_chars = await collection.count_documents({})


    progress_percent = (char_count / total_db_chars * 100) if total_db_chars > 0 else 0
    bar_len = 10
    filled = int(progress_percent / 100 * bar_len)
    progress_bar = "▰" * filled + "▱" * (bar_len - filled)


    progress = await get_user_progress(user_id)
    level = progress["level"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"].capitalize()
    xp_bar = get_progress_bar(xp_current, xp_needed, 10)


    active_pet = await get_active_pet(user_id)
    pet_text = html_escape(f"{active_pet['name']} (Lvl {active_pet.get('level', 1)})") if active_pet else "None"


    fav_id = user_data.get('favorites', [None])[0]
    fav_char = next((c for c in chars if str(c.get('id')) == str(fav_id)), None)
    fav_name = html_escape(fav_char['name']) if fav_char else "None"


    rarity_stats = {}
    for c in chars:
        r = c.get('rarity', '⚪ Common')
        rarity_stats[r] = rarity_stats.get(r, 0) + 1


    profile_text = (
        f"<b>🌟 {user_name}'s Profile 🌟</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🎫 <b>Battle Pass:</b> {pass_type}\n\n"
        f"⭐ <b>Level:</b> <code>{level}</code>\n"
        f"📊 <b>XP:</b> {xp_bar} <code>{xp_current}/{xp_needed}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Shards:</b> {user_balance:,} ⬪\n"
        f"<b>Zenith:</b> {zenith:,} ⧫\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🍱 <b>Collected:</b> {char_count}/{total_db_chars}\n"
        f"❤️ <b>Favorite:</b> <code>{fav_name}</code>\n"
        f"🐾 <b>Active Pet:</b> <code>{pet_text}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>📚 Collection By Rarity</b>\n"
    )

    for rarity, icon in RARITY_ICONS.items():
        count = rarity_stats.get(rarity, 0)
        rarity_name = rarity.split()[-1]
        profile_text += f"{icon} {rarity_name}: `{count}`\n"


    from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
    
    is_private = message.chat.type == enums.ChatType.PRIVATE
    builder = KeyboardBuilder()
    builder.add_button("View Harem", callback_data=f"harem_view:{user_id}", style=enums.ButtonStyle.PRIMARY)
    
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        builder.add_row(webapp_btn)

    reply_markup = builder.build()


    try:
        pic = random.choice(PHOTO_URL)
        await reply_media_dynamic(message, pic,
            caption=profile_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Profile Photo Error: {e}")
        await message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
