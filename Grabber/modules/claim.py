import random
from pyrogram import filters, types, enums, errors
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app
from Grabber import LOGGER
from Grabber.database import collection, user_collection
from Grabber.core.user import get_user_data, add_char_to_user, update_user
from Grabber.core.sessions import create_session, get_session

MUST_JOIN = "TNJBotSupport"
SECOND_JOIN = "SEAL_UPDATE"
DAILY_SHARD_REWARD = 200

RARITY_WEIGHTS = {
    '⚪ Common': 60,
    '🟢 Medium': 30,
    '🟠 Rare': 9,
    '🟡 Legendary': 1
}

async def get_weighted_rarity_character():
    rarity = random.choices(list(RARITY_WEIGHTS.keys()), weights=RARITY_WEIGHTS.values(), k=1)[0]
    cursor = collection.aggregate([{'$match': {'rarity': rarity}}, {'$sample': {'size': 1}}])
    res = await cursor.to_list(length=1)
    return res[0] if res else None

async def check_groups_joined(user_id: int) -> bool:
    try:
        await app.get_chat_member(MUST_JOIN, user_id)
        await app.get_chat_member(SECOND_JOIN, user_id)
        return True
    except errors.UserNotParticipant:
        return False
    except Exception as e:
        LOGGER.error(f"FZS Check Error: {e}")
        return False

@app.on_message(filters.command("claim"))
async def claim_handler(_, message: types.Message):
    user_id = message.from_user.id
    user = await get_user_data(user_id)

    if user and user.get('claimed_waifu'):
        return await message.reply_text("🎖️ <b>You already claimed your free waifu!</b>", parse_mode=ParseMode.HTML)

    if not await check_groups_joined(user_id):
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("✅ Group", url=f"t.me/{MUST_JOIN}"),
             types.InlineKeyboardButton("📢 Channel", url=f"t.me/{SECOND_JOIN}")],
            [types.InlineKeyboardButton("🔄 Verify & Claim", callback_data=f"clm_v:{user_id}")]
        ])
        return await message.reply_text(
            "🔒 <b>Join our channels to unlock your free waifu!</b>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )


    await show_preview(message, user_id)

async def show_preview(message_or_query, user_id):

    char = await get_weighted_rarity_character()
    if not char:
        error_msg = "⚠️ No characters found."
        if isinstance(message_or_query, types.CallbackQuery):
            return await message_or_query.message.edit_text(error_msg)
        else:
            return await message_or_query.reply_text(error_msg)


    await create_session(f"claim_{user_id}", {"character": char})

    preview_text = (
        f"🎁 <b>Your Free Character Preview!</b>\n\n"
        f"🆔 <b>ID:</b> <code>{char['id']}</code>\n"
        f"📛 <b>Name:</b> {html_escape(char['name'])}\n"
        f"🎬 <b>Anime:</b> {html_escape(char['anime'])}\n"
        f"✨ <b>Rarity:</b> {html_escape(char['rarity'])}\n\n"
        f"💰 <b>Bonus:</b> +{DAILY_SHARD_REWARD} Shards ⬪\n\n"
        f"<i>Click below to claim this character!</i>"
    )

    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("✅ Claim Now!", callback_data=f"clm_confirm:{user_id}")]
    ])

    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.delete()
            await app.send_photo(
                message_or_query.message.chat.id,
                char['img_url'],
                caption=preview_text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await message_or_query.reply_photo(
                char['img_url'],
                caption=preview_text,
                reply_markup=markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        LOGGER.error(f"Error in show_preview: {e}")

@app.on_callback_query(filters.regex(r"^clm_v:"))
async def claim_verify_handler(_, query: types.CallbackQuery):
    user_id = int(query.data.split(":")[1])
    if query.from_user.id != user_id:
        return await query.answer("❌ Not for you!", show_alert=True)

    await query.answer("Verifying...", cache_time=1)

    if await check_groups_joined(user_id):

        await show_preview(query, user_id)
    else:
        await query.answer("❌ You haven't joined yet!", show_alert=True)

@app.on_callback_query(filters.regex(r"^clm_confirm:"))
async def claim_confirm_handler(_, query: types.CallbackQuery):
    user_id = int(query.data.split(":")[1])
    if query.from_user.id != user_id:
        return await query.answer("❌ Not for you!", show_alert=True)


    session = await get_session(f"claim_{user_id}")
    if not session or "character" not in session:
        return await query.answer("⚠️ Session expired. Use /claim again.", show_alert=True)

    char = session["character"]


    await add_char_to_user(user_id, char)
    await update_user(user_id, {
        "$set": {"claimed_waifu": True},
        "$inc": {"balance": DAILY_SHARD_REWARD}
    })

    caption = (
        f'🎉 <a href="tg://user?id={query.from_user.id}">{html_escape(query.from_user.first_name)}</a> claimed their free waifu!\n\n'
        f"🆔 <b>ID:</b> <code>{char['id']}</code>\n"
        f"📛 <b>Name:</b> {html_escape(char['name'])}\n"
        f"🎬 <b>Anime:</b> {html_escape(char['anime'])}\n"
        f"✨ <b>Rarity:</b> {html_escape(char['rarity'])}\n\n"
        f"💰 <b>Bonus Received:</b> +{DAILY_SHARD_REWARD} Shards ⬪"
    )

    try:
        await query.message.edit_caption(caption=caption, parse_mode=ParseMode.HTML)
        await query.answer("✅ Successfully claimed!", show_alert=True)
    except Exception as e:
        LOGGER.error(f"Error in claim_confirm: {e}")
        await query.answer("✅ Claimed!", show_alert=True)
