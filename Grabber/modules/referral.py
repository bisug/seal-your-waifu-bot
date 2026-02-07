from pyrogram import filters, types, enums
from Grabber import app, user_collection, BOT_USERNAME

@app.on_message(filters.command("referrals"))
async def referrals_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    
    if not user:
        await message.reply_text("❌ You need to start the bot first!")
        return

    # Get stats
    referrals_count = user.get("referrals_count", 0)
    earned_coins = user.get("referrals_earned", 0)
    
    # Generate Link
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    text = (
        f"🤝 **Your Referral Stats**\n\n"
        f"👥 **Invited Users:** `{referrals_count}`\n"
        f"💰 **Coins Earned:** `{earned_coins}`\n\n"
        f"🔗 **Your Link:**\n`{ref_link}`\n\n"
        f"**Rewards:**\n"
        f"🔸 You get: **500 Coins** + **50 XP**\n"
        f"🔹 They get: **1,500 Coins** + **Level 10 Pet!** 🦊"
    )
    
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)
