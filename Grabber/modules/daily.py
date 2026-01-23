import random
from datetime import datetime, timezone
from pyrogram import filters, enums, types
from Grabber.app import app
from Grabber import SUPPORT_GROUP_ID, LOGGER
from Grabber.core.user import get_user_data, add_char_to_user, update_user
from Grabber.database import collection

RARITY_WEIGHTS = {
    '⚪ Common': 60,
    '🟢 Medium': 30,
    '🟠 Rare': 9,
    '🟡 Legendary': 1
}

async def get_daily_waifu():
    rarity = random.choices(list(RARITY_WEIGHTS.keys()), weights=RARITY_WEIGHTS.values(), k=1)[0]
    cursor = collection.aggregate([{'$match': {'rarity': rarity}}, {'$sample': {'size': 1}}])
    res = await cursor.to_list(length=1)
    return res[0] if res else None

@app.on_message(filters.command("daily_claim") & filters.group)
async def daily_claim_handler(_, message: types.Message):
    if message.chat.id != SUPPORT_GROUP_ID:
        return await message.reply_text("❌ This command only works in the support group.")

    user_id = message.from_user.id
    user = await get_user_data(user_id)
    
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user and user.get('last_daily_claim_date') == now_date:
        return await message.reply_text("⏳ You've already claimed your daily character today!")

    await app.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
    char = await get_daily_waifu()
    
    if not char:
        return await message.reply_text("⚠️ No characters available currently.")

    await add_char_to_user(user_id, char)
    await update_user(user_id, {"$set": {"last_daily_claim_date": now_date}})

    caption = (
        f"🎊 {message.from_user.mention} claimed their daily character!\n\n"
        f"📛 **Name:** {char['name']}\n"
        f"✨ **Rarity:** {char['rarity']}\n"
        f"🎬 **Anime:** {char['anime']}"
    )

    await message.reply_photo(char['img_url'], caption=caption)
