import random
import string
from pyrogram import enums, filters, types

from config import config
from backend import (LOGGER, MAIN_GROUP_ID, OWNER_ID, app, collection)
from backend.core.sessions import create_session, delete_session, get_session
from backend.core.utils import handle_errors, html_escape, reply_media_dynamic
from backend.core.user import add_char_to_user
from backend.core.cache import sync_user_to_redis
def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
async def process_core_claim(client, user, code: str):
    """Core logic to process a claim safely. Prevents double-dips and handles DB/Cache."""
    user_id = user.id
    details = await get_session(f"gen_{code}")
    if not details:
        return False, "❌ Invalid or expired code."
    if details['quantity'] <= 0:
        return False, "❌ This code has hit its maximum claim limit."
    claimed_by = details.get('claimed_by', [])
    if user_id in claimed_by:
        return False, "❌ You have already claimed this reward!"
    waifu = details['waifu']
    # 1. Update Database Safely
    await add_char_to_user(user_id, waifu)
    # 2. Sync WebApp Data
    await sync_user_to_redis(user_id)
    # 3. Update Session State
    claimed_by.append(user_id)
    new_quantity = details['quantity'] - 1
    if new_quantity == 0:
        await delete_session(f"gen_{code}")
    else:
        details['quantity'] = new_quantity
        details['claimed_by'] = claimed_by
        await create_session(f"gen_{code}", details, ttl=86400 * 7)
    # 4. Log Action
    log_text = (
        f'🎁 <b>Reward Claimed</b>\n'
        f'Claimer: <a href="tg://user?id={user.id}">{html_escape(user.first_name)}</a> (<code>{user_id}</code>)\n'
        f"Code: <code>{code}</code>\n"
        f"Character: {waifu['name']} | {waifu['rarity']}\n"
        f"Remaining quantity: {new_quantity}"
    )
    try:
        await client.send_message(chat_id=MAIN_GROUP_ID, text=log_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Log sending failed in giveaway: {e}")
    return True, waifu
@app.on_message(filters.command("waifugen") & filters.user(OWNER_ID))
@handle_errors
async def waifugen(_, message: types.Message):
    if len(message.command) != 3:
        return await message.reply_text("Invalid usage. Usage: <code>/waifugen &lt;waifu_id&gt; &lt;quantity&gt;</code>", parse_mode=enums.ParseMode.HTML)
    try:
        waifu_id = message.command[1]
        quantity = int(message.command[2])
    except ValueError:
        return await message.reply_text("Invalid quantity. Please enter a number.", parse_mode=enums.ParseMode.HTML)
    if quantity <= 0:
        return await message.reply_text("Quantity must be greater than 0.")
    waifu = await collection.find_one({'id': waifu_id})
    if not waifu:
        return await message.reply_text("Invalid waifu ID.", parse_mode=enums.ParseMode.HTML)
    code = generate_random_code()
    # Track quantity and who claimed it to prevent double-dipping
    await create_session(f"gen_{code}", {
        'waifu': waifu, 
        'quantity': quantity,
        'claimed_by': []
    }, ttl=86400 * 7)
    bot_username = config.BOT_USERNAME or (await app.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=claim_{code}"
    response_text = (
        f"✅ <b>Giveaway Generated!</b>\n\n"
        f"<b>Code:</b> <code>{code}</code>\n"
        f"<b>Redeem:</b> <code>/reedem {code}</code>\n"
        f"<b>Quantity:</b> {quantity}\n"
        f"<b>Character:</b> {html_escape(waifu['name'])} ({html_escape(waifu['rarity'])})\n\n"
        f"🔗 <b>Claim Link:</b>\n{deep_link}\n\n"
        f"<i>Post this link to let users claim their reward instantly!</i>"
    )
    await message.reply_text(response_text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    # Log to admin group
    log_text = (
        f'🎟 <b>Giveaway Created</b> by <a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>\n'
        f"Code: <code>{code}</code>\n"
        f"Character: {waifu['name']} | <code>{waifu['id']}</code>\n"
        f"Copies: {quantity}"
    )
    try:
        await app.send_message(chat_id=MAIN_GROUP_ID, text=log_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Log sending failed: {e}")
@app.on_message(filters.command(["reedem", "redeem", "claimwaifu"]))
@handle_errors
async def redeem_waifu(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: <code>/reedem &lt;code&gt;</code>", parse_mode=enums.ParseMode.HTML)
    code = message.command[1].strip().lower()
    success, result = await process_core_claim(app, message.from_user, code)
    if not success:
        return await message.reply_text(result, parse_mode=enums.ParseMode.HTML)
    waifu = result
    response_text = (
        f'🎉 Congratulations <a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>!\n'
        f"You claimed a <b>{html_escape(waifu['rarity'])}</b> character!\n\n"
        f"Name: {html_escape(waifu['name'])}\n"
        f"Anime: {html_escape(waifu['anime'])}\n"
        f"ID: <code>{waifu['id']}</code>\n"
    )
    await reply_media_dynamic(message, waifu['img_url'], caption=response_text, parse_mode=enums.ParseMode.HTML)
@app.on_message(filters.command("drop") & filters.user(OWNER_ID))
@handle_errors
async def drop_waifu(_, message: types.Message):
    """Summons a waifu directly into chat for users to claim via inline button."""
    if len(message.command) != 3:
        return await message.reply_text("Usage: <code>/drop &lt;waifu_id&gt; &lt;quantity&gt;</code>", parse_mode=enums.ParseMode.HTML)
    try:
        waifu_id = message.command[1]
        quantity = int(message.command[2])
    except ValueError:
        return await message.reply_text("Quantity must be a number.", parse_mode=enums.ParseMode.HTML)
    waifu = await collection.find_one({'id': waifu_id})
    if not waifu:
        return await message.reply_text("Invalid waifu ID.", parse_mode=enums.ParseMode.HTML)
    code = generate_random_code()
    await create_session(f"gen_{code}", {
        'waifu': waifu, 
        'quantity': quantity,
        'initial_quantity': quantity,
        'claimed_by': []
    }, ttl=86400 * 7)
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton(f"🎁 Claim Reward (0/{quantity})", callback_data=f"drop_{code}")]
    ])
    caption = (
        f"🚨 <b>A WILD DROP APPEARED!</b> 🚨\n\n"
        f"<b>Character:</b> {html_escape(waifu['name'])}\n"
        f"<b>Rarity:</b> {html_escape(waifu['rarity'])}\n\n"
        f"<i>Quick! Click the button below to claim!</i>"
    )
    await reply_media_dynamic(message, waifu['img_url'], caption=caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
@app.on_callback_query(filters.regex(r"^drop_(.*)"))
async def process_drop_claim(client, query: types.CallbackQuery):
    code = query.data.split("_")[1]
    success, result = await process_core_claim(client, query.from_user, code)
    if not success:
        return await query.answer(result, show_alert=True)
    waifu = result
    # Check updated state to modify the button
    details = await get_session(f"gen_{code}")
    if not details:
        # Fully claimed
        await query.answer(f"🎉 You got the last one!", show_alert=True)
        try:
            await query.message.edit_reply_markup(types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton(f"✅ Fully Claimed", callback_data="dead_btn")]
            ]))
        except Exception:
            pass
    else:
        # Still remaining
        claimed_count = len(details.get('claimed_by', []))
        total_count = details.get('initial_quantity', claimed_count + details['quantity'])
        await query.answer(f"🎉 You successfully claimed {waifu['name']}!", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton(f"🎁 Claim Reward ({claimed_count}/{total_count})", callback_data=f"drop_{code}")]
            ])
            await query.message.edit_reply_markup(markup)
        except Exception:
            pass
