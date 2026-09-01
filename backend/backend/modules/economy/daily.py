from datetime import datetime, timedelta, timezone

from pymongo.errors import DuplicateKeyError
from pyrogram import enums, filters, types

from backend.client import app
from backend.core.cache import (
    get_daily_date,
    get_weekly_date,
    invalidate_leaderboard_cache,
    invalidate_user_cache,
    set_daily_date,
    set_weekly_date,
    sync_user_to_redis,
)
from backend.core.pass_config import PASS_BENEFITS, get_active_pass_type
from backend.core.rarities import CLAIM_RARITY_WEIGHTS, weighted_pick
from backend.core.roles import apply_role_bonus
from backend.core.user import add_user_set_on_insert, get_user_data
from backend.core.utils import get_user_id_query, handle_errors, html_escape, reply_media_dynamic
from backend.core.waifu import sample_character_by_rarity
from backend.database import user_collection
from config import config

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
    rarity = weighted_pick(CLAIM_RARITY_WEIGHTS)
    if rarity is None:
        return None
    return await sample_character_by_rarity(rarity)
@app.on_message(filters.command("daily"))
@handle_errors
async def daily_command_handler(_, message: types.Message):
    # Full reward in the main group; 0.6x elsewhere so private/web-app
    # users still earn passively.
    in_main = message.chat.id == config.MAIN_GROUP_ID
    reward_mult = 1.0 if in_main else 0.6
    pm_note = "" if in_main else "\n\n<i>Tip: claim /daily in the main group for full rewards!</i>"
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    user = user or {}
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_claim_date = await get_daily_date(user_id)
    if last_claim_date is None:
        last_claim_date = user.get('last_daily_date')
    if last_claim_date == now_date:
        return await message.reply_text("You've already claimed your daily reward today!", parse_mode=enums.ParseMode.HTML)
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
    pass_type = get_active_pass_type(user)
    multiplier = PASS_BENEFITS[pass_type]["daily_multiplier"]
    base_coins = reward_coins
    reward_coins = int(base_coins * multiplier * reward_mult)
    bonus_coins = reward_coins - base_coins
    # reward_mult=0.6 outside the main group can make the bonus negative.
    pass_bonus_text = f"\n<b>Pass Bonus:</b> +{bonus_coins} ⬪" if multiplier > 1.0 and bonus_coins > 0 else ""
    reward_coins, staff_bonus = apply_role_bonus(user_id, reward_coins, "daily_bonus_percent")
    staff_bonus_text = f"\n<b>Staff Bonus:</b> +{staff_bonus} ⬪" if staff_bonus else ""
    char = await get_daily_waifu()
    if not char:
        return await message.reply_text("No characters available currently.", parse_mode=enums.ParseMode.HTML)
    claim_filter = get_user_id_query(user_id)
    claim_filter["last_daily_date"] = {"$ne": now_date}
    try:
        claim_result = await user_collection.update_one(
            claim_filter,
            add_user_set_on_insert({
                "$set": {"last_daily_date": now_date, "daily_streak": streak},
                "$inc": {"balance": reward_coins, "char_count": 1, "version": 1},
                "$push": {"characters": char},
                "$setOnInsert": {"id": user_id}
            }, user_id, first_name=message.from_user.first_name, username=message.from_user.username),
            upsert=True
        )
    except DuplicateKeyError:
        # Concurrent claim won the race; the unique id index blocked the insert.
        return await message.reply_text("You've already claimed your daily reward today!", parse_mode=enums.ParseMode.HTML)
    if claim_result.modified_count == 0 and claim_result.upserted_id is None:
        return await message.reply_text("You've already claimed your daily reward today!", parse_mode=enums.ParseMode.HTML)
    await set_daily_date(user_id, now_date)
    await invalidate_user_cache(user_id)
    await invalidate_leaderboard_cache()
    await sync_user_to_redis(user_id)
    caption = (
        f'<a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a> claimed their daily reward!\n\n'
        f"<b>Character:</b> {html_escape(char['name'])}\n"
        f"<b>Rarity:</b> {html_escape(char['rarity'])}\n"
        f"<b>Anime:</b> {html_escape(char['anime'])}\n\n"
        f"<b>Coins:</b> +{reward_coins} ⬪{pass_bonus_text}{staff_bonus_text}\n"
        f"<b>Streak:</b> {streak}/7 Days{pm_note}"
    )
    await reply_media_dynamic(message, char['img_url'], caption=caption, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("weekly"))
@handle_errors
async def weekly_command_handler(_, message: types.Message):
    # Full reward in the main group; 0.6x elsewhere (see /daily).
    in_main = message.chat.id == config.MAIN_GROUP_ID
    reward_mult = 1.0 if in_main else 0.6
    pm_note = "" if in_main else "\n\n<i>Tip: claim /weekly in the main group for full rewards!</i>"
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    user = user or {}
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d")
    last_weekly_cached = await get_weekly_date(user_id)
    last_weekly = last_weekly_cached or user.get('last_weekly_date')
    if last_weekly:
        last_date = datetime.strptime(last_weekly, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_diff = (now - last_date).days
        if days_diff < 7:
            return await message.reply_text(f"You can claim your weekly reward again in {7 - days_diff} days.", parse_mode=enums.ParseMode.HTML)
    pass_type = get_active_pass_type(user)
    multiplier = PASS_BENEFITS[pass_type]["weekly_multiplier"]
    base_coins = 2000
    reward_coins = int(base_coins * multiplier * reward_mult)
    xp_reward = int(500 * PASS_BENEFITS[pass_type]["xp_multiplier"])
    bonus_coins = reward_coins - base_coins
    pass_bonus_text = f"\n(+{bonus_coins} Pass Bonus)" if multiplier > 1.0 and bonus_coins > 0 else ""
    reward_coins, staff_coin_bonus = apply_role_bonus(user_id, reward_coins, "weekly_bonus_percent")
    xp_reward, staff_xp_bonus = apply_role_bonus(user_id, xp_reward, "weekly_xp_bonus_percent")
    staff_coin_text = f"\n(+{staff_coin_bonus:,} Staff Bonus)" if staff_coin_bonus else ""
    staff_xp_text = f"\n(+{staff_xp_bonus:,} Staff XP)" if staff_xp_bonus else ""
    weekly_filter = get_user_id_query(user_id)
    weekly_filter["$or"] = [
        {"last_weekly_date": {"$exists": False}},
        {"last_weekly_date": {"$lte": (now - timedelta(days=7)).strftime("%Y-%m-%d")}}
    ]
    try:
        weekly_result = await user_collection.update_one(
            weekly_filter,
            add_user_set_on_insert({
                "$set": {"last_weekly_date": now_str},
                "$inc": {"balance": reward_coins, "version": 1},
                "$setOnInsert": {"id": user_id}
            }, user_id, first_name=message.from_user.first_name, username=message.from_user.username),
            upsert=True
        )
    except DuplicateKeyError:
        # Concurrent claim won the race; the unique id index blocked the insert.
        return await message.reply_text("You have already claimed this weekly reward.", parse_mode=enums.ParseMode.HTML)
    if weekly_result.modified_count == 0 and weekly_result.upserted_id is None:
        return await message.reply_text("You have already claimed this weekly reward.", parse_mode=enums.ParseMode.HTML)
    await set_weekly_date(user_id, now_str)
    await invalidate_user_cache(user_id)
    await invalidate_leaderboard_cache()
    await sync_user_to_redis(user_id)
    from backend.core.progression import add_xp
    await add_xp(user_id, xp_reward, "weekly_claim")
    await message.reply_text(
        f"<b>Weekly Reward Claimed!</b>\n\n"
        f"<b>Coins:</b> +{reward_coins} ⬪{pass_bonus_text}{staff_coin_text}\n"
        f"<b>XP:</b> +{xp_reward} XP{staff_xp_text}\n"
        f"Come back in 7 days!{pm_note}",
        parse_mode=enums.ParseMode.HTML
    )
