import math
import random

from pyrogram import enums, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import LOGGER, PHOTO_URL, WEB_APP_URL, app, user_collection
from Grabber.core.progression import get_progress_bar, get_user_progress
from Grabber.core.user import get_active_pet, get_user_data
from Grabber.core.utils import html_escape, reply_media_dynamic
from Grabber.database import collection

RARITY_ICONS = {
    'Common': '◌', 'Medium': '○', 'Rare': '◙',
    'Legendary': '◎', 'Cosmic': '◉', 'Exclusive': '◈',
    'Limited Edition': '▣'
}

@app.on_message(filters.command(["profile", "myprofile", "me", "status", "mystatus"]))
async def profile_handler(_, message: types.Message):
    """Generate and display the user's progress and collection profile."""
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        return await message.reply_text("<b>No profile found!</b> Try collecting a character first.", parse_mode=ParseMode.HTML)

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
        f"<b>Collector Profile: {user_name}</b>\n\n"
        f"<b>Collector ID:</b> <code>{user_id}</code>\n"
        f"<b>Battle Pass:</b> {pass_type}\n\n"
        f"<b>Level:</b> <code>{level}</code>\n"
        f"<b>XP:</b> {xp_bar} <code>{xp_current}/{xp_needed}</code>\n\n"
        f"<b>Shards:</b> {user_balance:,} ⬪\n"
        f"<b>Zenith:</b> {zenith:,} ⧫\n\n"
        f"<b>Collected:</b> {char_count}/{total_db_chars}\n"
        f"<b>Favorite:</b> <code>{fav_name}</code>\n"
        f"<b>Active Pet:</b> <code>{pet_text}</code>\n\n"
        f"<b>Collection By Rarity</b>\n"
    )

    for rarity_key, symbol in RARITY_ICONS.items():
        count = 0
        # Search for rarity with or without emoji prefix for compatibility
        for db_rarity, db_count in rarity_stats.items():
            if rarity_key in db_rarity:
                count += db_count
        profile_text += f"{symbol} {rarity_key}: `{count}`\n"


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
