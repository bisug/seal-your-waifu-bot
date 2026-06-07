from pyrogram import enums, filters, types

from config import config
from Grabber import app, user_collection
from Grabber.core.referrals import get_referral_stats
from Grabber.core.user import get_user_filter
from Grabber.core.utils import handle_errors

@app.on_message(filters.command("referrals"))
@handle_errors
async def referrals_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one(get_user_filter(user_id))
    if not user:
        await message.reply_text("You need to start the bot first!", parse_mode=enums.ParseMode.HTML)
        return
    stats = get_referral_stats(user)
    ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}"
    text = (
        f"<b>Your Referral Stats</b>\n\n"
        f"<b>Invited Users:</b> <code>{stats['invited_count']:,}</code>\n"
        f"<b>Shards Earned:</b> <code>{stats['earned_shards']:,}</code> ⬪\n\n"
        f"<b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
        f"<b>Rewards:</b>\n"
        f"◉ You get: <b>{stats['referrer_reward_shards']:,} ⬪</b> "
        f"+ <b>{stats['referrer_reward_xp']:,} XP</b>\n"
        f"◎ They get: <b>{stats['referred_reward_shards']:,} ⬪</b> "
        f"+ <b>Level {stats['referred_pet_level']} Pet!</b>"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
