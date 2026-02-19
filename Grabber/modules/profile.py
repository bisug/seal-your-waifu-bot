import math
from pyrogram import filters, types, enums
from Grabber import app, user_collection, PHOTO_URL, LOGGER
from Grabber.core.utils import md_escape
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
        return await message.reply_text("🚨 **No profile found!** Try collecting a character first.")

    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
                
    user_name = md_escape(message.from_user.first_name)
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
    pet_text = f"{active_pet['name']} (Lvl {active_pet.get('level', 1)})" if active_pet else "None"
    
                        
    fav_id = user_data.get('favorites', [None])[0]
    fav_char = next((c for c in chars if str(c.get('id')) == str(fav_id)), None)
    fav_name = fav_char['name'] if fav_char else "None"
    
                  
    rarity_stats = {}
    for c in chars:
        r = c.get('rarity', '⚪ Common')
        rarity_stats[r] = rarity_stats.get(r, 0) + 1

                           
    profile_text = (
        f"**🌟 {user_name}'s Profile 🌟**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"🎫 **Battle Pass:** {pass_type}\n\n"
        f"⭐ **Level:** `{level}`\n"
        f"📊 **XP:** {xp_bar} `{xp_current}/{xp_needed}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Shards:** {user_balance:,} ⬪\n"
        f"**Zenith:** {zenith:,} ⧫\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🍱 **Collected:** {char_count}/{total_db_chars}\n"
        f"❤️ **Favorite:** `{fav_name}`\n"
        f"🐾 **Active Pet:** `{pet_text}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"**📚 Collection By Rarity**\n"
    )
    
    for rarity, icon in RARITY_ICONS.items():
        count = rarity_stats.get(rarity, 0)
        rarity_name = rarity.split()[-1]
        profile_text += f"{icon} {rarity_name}: `{count}`\n"

             
    buttons = [
        [types.InlineKeyboardButton("🎒 Harem", callback_data=f"harem_view:{user_id}")]
    ]

                            
    try:
        pic = random.choice(PHOTO_URL)
        await message.reply_photo(
            photo=pic,
            caption=profile_text,
            reply_markup=types.InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        LOGGER.error(f"Profile Photo Error: {e}")
        await message.reply_text(profile_text, reply_markup=types.InlineKeyboardMarkup(buttons))
