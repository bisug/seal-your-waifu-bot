import random
from datetime import datetime, timedelta, timezone
from pyrogram import filters, enums, types
from pyrogram.enums import ParseMode
from Grabber.core.utils import md_escape
from Grabber import app
from Grabber import SUPPORT_GROUP_ID, LOGGER
from Grabber.core.user import get_user_data, add_char_to_user, update_user
from Grabber.database import collection

RARITY_WEIGHTS = {
    '⚪ Common': 60,
    '🟢 Medium': 30,
    '🟠 Rare': 9,
    '🟡 Legendary': 1
}

# Rewards for streaks (Coins)
STREAK_REWARDS = {
    1: 100,
    2: 200,
    3: 300,
    4: 400,
    5: 500,
    6: 600,
    7: 1000  # Big reward for 7 days
}

async def get_daily_waifu():
    rarity = random.choices(list(RARITY_WEIGHTS.keys()), weights=RARITY_WEIGHTS.values(), k=1)[0]
    cursor = collection.aggregate([{'$match': {'rarity': rarity}}, {'$sample': {'size': 1}}])
    res = await cursor.to_list(length=1)
    return res[0] if res else None

@app.on_message(filters.command("daily") & filters.group)
async def daily_command_handler(_, message: types.Message):
    if message.chat.id != SUPPORT_GROUP_ID:
        return await message.reply_text("❌ This command only works in the support group.", parse_mode=ParseMode.MARKDOWN)

    user_id = message.from_user.id
    user = await get_user_data(user_id)
    
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_claim_date = user.get('last_daily_date')
    
    if last_claim_date == now_date:
        return await message.reply_text("⏳ You've already claimed your daily reward today!", parse_mode=ParseMode.MARKDOWN)
    
    # Calculate Streak
    streak = user.get('daily_streak', 0)
    yesterday_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if last_claim_date == yesterday_date:
        streak += 1
    else:
        streak = 1
        
    if streak > 7:
        streak = 1 # Reset after 7 days? Or Cap at 7? Let's Cap at 7 for max rewards but keep counting?
        # Actually user requested "Adjust Daily Streak Cap to 7 days" in task.md
        # If user misses a day, streak resets. If user maintains, it cycles? 
        # Typically games cycle 1-7. Let's cycle.
    
    reward_coins = STREAK_REWARDS.get(streak, 100)
    
    # Give Rewards
    await app.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
    char = await get_daily_waifu()
    
    if not char:
        return await message.reply_text("⚠️ No characters available currently.", parse_mode=ParseMode.MARKDOWN)

    # Update User
    await add_char_to_user(user_id, char)
    await update_user(user_id, {
        "$set": {"last_daily_date": now_date, "daily_streak": streak},
        "$inc": {"balance": reward_coins}
    })

    caption = (
        fr"🎊 {message.from_user.mention} claimed their daily reward\!\n\n"
        f"📛 **Character:** {md_escape(char['name'])}\n"
        f"✨ **Rarity:** {md_escape(char['rarity'])}\n"
        f"🎬 **Anime:** {md_escape(char['anime'])}\n\n"
        f"💰 **Coins:** +{reward_coins} ⬪\n"
        f"🔥 **Streak:** {streak}/7 Days"
    )

    await message.reply_photo(char['img_url'], caption=caption, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("weekly") & filters.group)
async def weekly_command_handler(_, message: types.Message):
    if message.chat.id != SUPPORT_GROUP_ID:
        return await message.reply_text("❌ This command only works in the support group.", parse_mode=ParseMode.MARKDOWN)

    user_id = message.from_user.id
    user = await get_user_data(user_id)
    
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d")
    if last_weekly:
        last_date = datetime.strptime(last_weekly, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_diff = (now - last_date).days
        if days_diff < 7:
            return await message.reply_text(f"⏳ You can claim your weekly reward again in {7 - days_diff} days.", parse_mode=ParseMode.MARKDOWN)
    
    # Weekly Rewards: 2000 Coins + 1 Rare Character (guaranteed?)
    # or just random better loot.
    # Let's give 2000 coins + 500 XP
    
    await update_user(user_id, {
        "$set": {"last_weekly_date": now_str},
        "$inc": {"balance": 2000}
    })
    
    # Also give XP
    from Grabber.core.progression import add_xp
    await add_xp(user_id, 500, "weekly_claim")
    
    await message.reply_text(
        f"🎁 **Weekly Reward Claimed!**\n\n"
        f"💰 **Coins:** +2,000 ⬪\n"
        f"🆙 **XP:** +500 XP\n"
        f"✅ Come back in 7 days!",
        parse_mode=ParseMode.MARKDOWN
    )
