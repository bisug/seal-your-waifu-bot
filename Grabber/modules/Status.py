import math
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber.core.user import get_user_data
from Grabber.database import collection

RARITY_ICONS = {
    '⚪ Common': '⚪', '🟢 Medium': '🟢', '🟠 Rare': '🟠',
    '🟡 Legendary': '🟡', '💠 Cosmic': '💠', '💮 Exclusive': '💮',
    '🔮 Limited Edition': '🔮'
}

@app.on_message(filters.command(["status", "mystatus"]))
async def status_handler(_, message: types.Message):
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    
    if not user:
        return await message.reply_text("❌ No profile found.")

    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
    chars = user.get('characters', [])
    char_count = len(chars)
    total_db_chars = await collection.count_documents({})
    
    progress = (char_count / total_db_chars * 100) if total_db_chars > 0 else 0
    bar_len = 10
    filled = int(progress / 100 * bar_len)
    bar = "▰" * filled + "▱" * (bar_len - filled)

    # Rarity counting
    stats = {}
    for c in chars:
        r = c.get('rarity', '⚪ Common')
        stats[r] = stats.get(r, 0) + 1

    text = (
        f"📊 **{message.from_user.first_name}'s Status**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **Balance:** {user.get('balance', 0)} coins\n"
        f"🍱 **Collected:** {char_count}/{total_db_chars}\n"
        f"📈 **Progress:** [{bar}] {progress:.1f}%\n"
        f"━━━━━━━━━━━━━━━━━━\n"
    )

    for rarity, icon in RARITY_ICONS.items():
        count = stats.get(rarity, 0)
        text += f"{icon} {rarity.split()[-1]}: `{count}`\n"

    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)
