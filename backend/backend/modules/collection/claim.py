import random
from pyrogram import enums, errors, filters, types
from pyrogram.errors import FloodWait
from pymongo.errors import DuplicateKeyError
from config import config
from backend import LOGGER, app
from backend.core.cache import sync_user_to_redis
from backend.core.sessions import create_session, get_session
from backend.core.user import add_user_set_on_insert, get_user_data
from backend.core.utils import (get_user_id_query, handle_errors, html_escape,
                                reply_media_dynamic, send_media_dynamic)
from backend.core.rarities import CLAIM_RARITY_WEIGHTS
from backend.database import collection, user_collection
# Fetch requirements from centralized config
MUST_JOIN = config.SUPPORT_CHAT
SECOND_JOIN = config.UPDATE_CHAT
DAILY_SHARD_REWARD = 500
async def get_weighted_rarity_character():
    rarity = random.choices(list(CLAIM_RARITY_WEIGHTS.keys()), weights=CLAIM_RARITY_WEIGHTS.values(), k=1)[0]
    cursor = await collection.aggregate([{'$match': {'rarity': rarity}}, {'$sample': {'size': 1}}])
    res = await cursor.to_list(length=1)
    return res[0] if res else None
async def check_groups_joined(user_id: int) -> bool:
    try:
        await app.get_chat_member(MUST_JOIN, user_id)
        await app.get_chat_member(SECOND_JOIN, user_id)
        return True
    except errors.UserNotParticipant:
        return False  # Definitive: user is not a member
    except FloodWait as e:
        LOGGER.warning(f"FloodWait during membership check for {user_id}: {e.value}s")
        return True   # Fail-open: don't punish user for our rate limit
    except Exception as e:
        LOGGER.error(f"Membership check error for {user_id}: {e}")
        return True   # Fail-open: ambiguous error, let the user proceed
@app.on_message(filters.command("claim"))
@handle_errors
async def claim_handler(_, message: types.Message):
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    if user and user.get('claimed_waifu'):
        return await message.reply_text("<b>You already claimed your free waifu!</b>", parse_mode=enums.ParseMode.HTML)
    if not await check_groups_joined(user_id):
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("Join Updates", url=f"t.me/{SECOND_JOIN}"),
             types.InlineKeyboardButton("Support Center", url=f"t.me/{MUST_JOIN}")],
            [types.InlineKeyboardButton("Verify & Claim", callback_data=f"clm_v:{user_id}")]
        ])
        return await message.reply_text(
            "<b>Authorization Required</b>\n\n"
            "To unlock your <b>Free Starter Waifu</b> and bonus Shards, please join our official sectors below.",
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
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
        f"<b>Your Free Character Preview!</b>\n\n"
        f"<b>ID:</b> <code>{char['id']}</code>\n"
        f"<b>Name:</b> {html_escape(char['name'])}\n"
        f"<b>Anime:</b> {html_escape(char['anime'])}\n"
        f"<b>Rarity:</b> {html_escape(char['rarity'])}\n\n"
        f"<b>Bonus:</b> +{DAILY_SHARD_REWARD} Shards ⬪\n\n"
        f"<i>Click below to claim this character!</i>"
    )
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("Claim Now!", callback_data=f"clm_confirm:{user_id}")]
    ])
    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.delete()
            await send_media_dynamic(app, message_or_query.message.chat.id, media_url=char['img_url'],
                caption=preview_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await reply_media_dynamic(message_or_query, char['img_url'],
                caption=preview_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
    except Exception as e:
        LOGGER.error(f"Error in show_preview: {e}")
@app.on_callback_query(filters.regex(r"^clm_v:"))
async def claim_verify_handler(_, query: types.CallbackQuery):
    user_id = int(query.data.split(":")[1])
    if query.from_user.id != user_id:
        return await query.answer("Not for you!", show_alert=True)
    await query.answer("Verifying...", cache_time=1)
    if await check_groups_joined(user_id):
        await show_preview(query, user_id)
    else:
        await query.answer("You haven't joined yet!", show_alert=True)
@app.on_callback_query(filters.regex(r"^clm_confirm:"))
async def claim_confirm_handler(_, query: types.CallbackQuery):
    user_id = int(query.data.split(":")[1])
    if query.from_user.id != user_id:
        return await query.answer("Not for you!", show_alert=True)
    session = await get_session(f"claim_{user_id}")
    if not session or "character" not in session:
        return await query.answer("Session expired. Use /claim again.", show_alert=True)
    char = session["character"]
    claim_filter = get_user_id_query(user_id)
    claim_filter["claimed_waifu"] = {"$ne": True}
    try:
        claim_result = await user_collection.update_one(
            claim_filter,
            add_user_set_on_insert({
                "$set": {"claimed_waifu": True},
                "$inc": {"balance": DAILY_SHARD_REWARD, "char_count": 1, "version": 1},
                "$push": {"characters": char},
                "$setOnInsert": {"id": user_id}
            }, user_id, first_name=query.from_user.first_name, username=query.from_user.username),
            upsert=True
        )
    except DuplicateKeyError:
        # Concurrent claim won the race; the unique id index blocked the insert.
        return await query.answer("You already claimed your free waifu!", show_alert=True)
    if claim_result.modified_count == 0 and claim_result.upserted_id is None:
        return await query.answer("You already claimed your free waifu!", show_alert=True)
    mention = f'<a href="tg://user?id={query.from_user.id}">{html_escape(query.from_user.first_name)}</a>'
    caption = (
        f'{mention} claimed their **Free Starter Character**!\n\n'
        f"<b>ID:</b> <code>{char['id']}</code>\n"
        f"<b>Name:</b> {html_escape(char['name'])}\n"
        f"<b>Anime:</b> {html_escape(char['anime'])}\n"
        f"<b>Rarity:</b> {html_escape(char['rarity'])}\n\n"
        f"<b>Bonus:</b> +{DAILY_SHARD_REWARD} Shards ⬪\n\n"
        f"<i>Start your journey by checking your /harem!</i>"
    )
    try:
        await query.message.edit_caption(caption=caption, parse_mode=enums.ParseMode.HTML)
        await query.answer("Successfully claimed!", show_alert=True)
        # Ensure WebApp is synced immediately
        await sync_user_to_redis(user_id)
    except errors.MessageNotModified:
        await query.answer("Successfully claimed!", show_alert=True)
    except Exception as e:
        LOGGER.error(f"Error in claim_confirm: {e}")
        await query.answer("Claimed! check your /harem.", show_alert=True)
