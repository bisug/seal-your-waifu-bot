import random
from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import LOGGER
from Grabber.database import collection, user_collection
from Grabber.core.user import get_user_data, add_char_to_user, update_user

MUST_JOIN = "TNJBotSupport"
SECOND_JOIN = "SEAL_UPDATE"

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
        return await message.reply_text("🎖️ **You already claimed your free waifu!**")

    if not await check_groups_joined(user_id):
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("✅ Group", url=f"t.me/{MUST_JOIN}"),
             types.InlineKeyboardButton("📢 Channel", url=f"t.me/{SECOND_JOIN}")],
            [types.InlineKeyboardButton("🔄 Verify & Claim", callback_data=f"clm_v:{user_id}")]
        ])
        return await message.reply_text(
            "🔒 <b>Join our channels to unlock your free waifu!</b>",
            reply_markup=markup,
            parse_mode=enums.ParseMode.HTML
        )

    await process_claim(message, user_id)

async def process_claim(message_obj, user_id):
    char = await get_weighted_rarity_character()
    if not char:
        return await (message_obj.edit_text("⚠️ No characters found.") if isinstance(message_obj, types.Message) else message_obj.message.edit_text("⚠️ No characters found."))

    await add_char_to_user(user_id, char)
    await update_user(user_id, {"$set": {"claimed_waifu": True}})

    caption = (
        f"🎉 {message_obj.from_user.mention} claimed a free waifu!\n\n"
        f"🆔 **ID:** `{char['id']}`\n"
        f"📛 **Name:** {char['name']}\n"
        f"🎬 **Anime:** {char['anime']}\n"
        f"✨ **Rarity:** {char['rarity']}"
    )

    try:
        if isinstance(message_obj, types.CallbackQuery):
            await message_obj.message.delete()
            await app.send_photo(message_obj.message.chat.id, char['img_url'], caption=caption, parse_mode=enums.ParseMode.HTML)
        else:
            await message_obj.reply_photo(char['img_url'], caption=caption, parse_mode=enums.ParseMode.HTML)
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in process_claim: {e}")

@app.on_callback_query(filters.regex(r"^clm_v:"))
async def claim_verify_handler(_, query: types.CallbackQuery):
    user_id = int(query.data.split(":")[1])
    if query.from_user.id != user_id:
        return await query.answer("❌ Not for you!", show_alert=True)

    # Instant feedback
    await query.answer("Verifying...", cache_time=1)

    if await check_groups_joined(user_id):
        await process_claim(query, user_id)
    else:
        await query.answer("❌ You haven't joined yet!", show_alert=True)
