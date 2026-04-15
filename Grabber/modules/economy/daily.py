import random
from datetime import datetime, timedelta, timezone

from pyrogram import enums, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, MAIN_GROUP_ID, app
from Grabber.core.cache import (get_daily_date, get_weekly_date,
                                invalidate_leaderboard_cache,
                                invalidate_user_cache, set_daily_date,
                                set_weekly_date)
from Grabber.core.user import add_char_to_user, get_user_data, update_user
from Grabber.core.utils import html_escape, reply_media_dynamic
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
    if message.chat.id != MAIN_GROUP_ID:
        return await message.reply_text("This command only works in the main group.", parse_mode=ParseMode.HTML)

    user_id = message.from_user.id
    user = await get_user_data(user_id)

    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check Redis first, fall back to DB
    last_claim_date = await get_daily_date(user_id)
    if last_claim_date is None:
        last_claim_date = user.get('last_daily_date')

    if last_claim_date == now_date:
        return await message.reply_text("You've already claimed your daily reward today!", parse_mode=ParseMode.HTML)

    # Calculate Streak
    streak = user.get('daily_streak', 0)
    yesterday_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    if last_claim_date == yesterday_date:
        streak += 1
    else:
        streak = 1

    # Cap streak for storage first, then derive reward streak
    if streak > 7:
        streak = 1  # Reset for next cycle
    reward_streak = min(streak, 7)

    reward_coins = STREAK_REWARDS.get(reward_streak, 100)
    
    # Add Pass bonus
    pass_type = user.get("pass_type", "free")
    multiplier = 1.5 if pass_type == "elite" else 1.2 if pass_type == "premium" else 1.0
    base_coins = reward_coins
    reward_coins = int(base_coins * multiplier)
    bonus_coins = reward_coins - base_coins
    pass_bonus_text = f"\n<b>Pass Bonus:</b> +{bonus_coins} ⬪" if multiplier > 1.0 else ""

    # Give Rewards
    char = await get_daily_waifu()

    if not char:
        return await message.reply_text("No characters available currently.", parse_mode=ParseMode.HTML)

    # Update User
    await add_char_to_user(user_id, char)
    await update_user(user_id, {
        "$set": {"last_daily_date": now_date, "daily_streak": streak},
        "$inc": {"balance": reward_coins}
    })
    # Update Redis caches
    await set_daily_date(user_id, now_date)
    await invalidate_user_cache(user_id)
    await invalidate_leaderboard_cache()

    caption = (
        f'<a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a> claimed their daily reward!\n\n'
        f"<b>Character:</b> {html_escape(char['name'])}\n"
        f"<b>Rarity:</b> {html_escape(char['rarity'])}\n"
        f"<b>Anime:</b> {html_escape(char['anime'])}\n\n"
        f"<b>Coins:</b> +{reward_coins} ⬪{pass_bonus_text}\n"
        f"<b>Streak:</b> {streak}/7 Days"
    )

    await reply_media_dynamic(message, char['img_url'], caption=caption, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("weekly") & filters.group)
async def weekly_command_handler(_, message: types.Message):
    if message.chat.id != MAIN_GROUP_ID:
        return await message.reply_text("This command only works in the main group.", parse_mode=ParseMode.HTML)

    user_id = message.from_user.id
    user = await get_user_data(user_id)

    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d")

    # Check Redis first
    last_weekly_cached = await get_weekly_date(user_id)
    last_weekly = last_weekly_cached or user.get('last_weekly_date')

    if last_weekly:
        last_date = datetime.strptime(last_weekly, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_diff = (now - last_date).days
        if days_diff < 7:
            return await message.reply_text(f"You can claim your weekly reward again in {7 - days_diff} days.", parse_mode=ParseMode.HTML)

    # Weekly Rewards: 2000 Coins + 1 Rare Character (guaranteed?)
    # or just random better loot.
    # Let's give 2000 coins + 500 XP

    pass_type = user.get("pass_type", "free")
    multiplier = 1.5 if pass_type == "elite" else 1.2 if pass_type == "premium" else 1.0
    base_coins = 2000
    reward_coins = int(base_coins * multiplier)
    xp_reward = int(500 * multiplier)
    bonus_coins = reward_coins - base_coins
    pass_bonus_text = f"\n(+{bonus_coins} Pass Bonus)" if multiplier > 1.0 else ""

    await update_user(user_id, {
        "$set": {"last_weekly_date": now_str},
        "$inc": {"balance": reward_coins}
    })
    await set_weekly_date(user_id, now_str)
    await invalidate_user_cache(user_id)
    await invalidate_leaderboard_cache()

    # Also give XP
    from Grabber.core.progression import add_xp
    await add_xp(user_id, xp_reward, "weekly_claim")

    await message.reply_text(
        f"<b>Weekly Reward Claimed!</b>\n\n"
        f"<b>Coins:</b> +{reward_coins} ⬪{pass_bonus_text}\n"
        f"<b>XP:</b> +{xp_reward} XP\n"
        f"Come back in 7 days!",
        parse_mode=ParseMode.HTML
    )
