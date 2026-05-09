from pyrogram import errors, enums, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import app, user_collection
from Grabber.core.utils import handle_errors


@app.on_message(filters.command("referrals"))
@handle_errors
async def referrals_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await message.reply_text("You need to start the bot first!", parse_mode=ParseMode.HTML)
        return


    referrals_count = user.get("referrals_count", 0)
    earned_coins = user.get("referrals_earned", 0)


    ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"<b>Your Referral Stats</b>\n\n"
        f"<b>Invited Users:</b> <code>{referrals_count}</code>\n"
        f"<b>Shards Earned:</b> <code>{earned_coins}</code> ⬪\n\n"
        f"<b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
        f"<b>Rewards:</b>\n"
        f"◉ You get: <b>500 ⬪</b> + <b>50 XP</b>\n"
        f"◎ They get: <b>1,500 ⬪</b> + <b>Level 10 Pet!</b>"
    )

    await message.reply_text(text, parse_mode=ParseMode.HTML)
