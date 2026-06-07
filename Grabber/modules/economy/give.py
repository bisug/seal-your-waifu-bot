from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, OWNER_ID, app, client, sudo_users, user_collection, sudo_filter
from Grabber.core.cache import invalidate_user_cache
from Grabber.core.user import add_user_set_on_insert
from Grabber.core.utils import get_user_id_query, handle_errors, html_escape
from Grabber.modules.progression.achievements import check_achievements
from Grabber.modules.progression.quests import update_quest_progress
@app.on_message(filters.command("givebalance"))
@handle_errors
async def give_balance(_, message: types.Message):
    sender_id = message.from_user.id
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to give balance.")
        return
    recipient = message.reply_to_message.from_user
    recipient_id = recipient.id
    try:
        if len(message.command) < 2:
            raise ValueError
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (IndexError, ValueError):
        await message.reply_text("Usage: <code>/givebalance &lt;amount&gt;</code> (Reply to user)", parse_mode=enums.ParseMode.HTML)
        return
    if sender_id in sudo_users or sender_id == OWNER_ID:
        await user_collection.update_one(
            get_user_id_query(recipient_id),
            add_user_set_on_insert(
                {'$inc': {'balance': amount}, '$setOnInsert': {'id': recipient_id}},
                recipient_id,
                first_name=recipient.first_name,
                username=recipient.username,
            ),
            upsert=True
        )
        await invalidate_user_cache(recipient_id)
        await message.reply_text(f"{amount} ⬪ given to {html_escape(recipient.first_name)}!")
        LOGGER.info(f"ADMIN {sender_id} gave {amount} to {recipient_id}")
        return
    try:
        async with await client.start_session() as mongo_session:
            async with mongo_session.start_transaction():
                sender_filter = get_user_id_query(sender_id)
                sender_filter['balance'] = {'$gte': amount}
                res = await user_collection.update_one(
                    sender_filter,
                    {'$inc': {'balance': -amount, 'version': 1}},
                    session=mongo_session
                )
                if res.modified_count == 0:
                    raise ValueError("Insufficient balance to give.")
                await user_collection.update_one(
                    get_user_id_query(recipient_id),
                    add_user_set_on_insert(
                        {'$inc': {'balance': amount, 'version': 1}, '$setOnInsert': {'id': recipient_id}},
                        recipient_id,
                        first_name=recipient.first_name,
                        username=recipient.username,
                    ),
                    upsert=True,
                    session=mongo_session
                )
    except ValueError as e:
        await message.reply_text(str(e))
        return
    await invalidate_user_cache(sender_id)
    await invalidate_user_cache(recipient_id)
    await message.reply_text(f"You gave {amount} ⬪ to {html_escape(recipient.first_name)}!")
    LOGGER.info(f"User {sender_id} gave {amount} to {recipient_id}")
    await update_quest_progress(sender_id, "generous_soul", 1)
    await check_achievements(sender_id)
@app.on_message(filters.command("takebalance"))
@handle_errors
async def take_balance(_, message: types.Message):
    sender_id = message.from_user.id
    if sender_id not in sudo_users and sender_id != OWNER_ID:
        await message.reply_text("You are not authorized to take balance.")
        return
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to take balance from.")
        return
    recipient = message.reply_to_message.from_user
    recipient_id = recipient.id
    try:
        if len(message.command) < 2:
            raise ValueError
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (IndexError, ValueError):
        await message.reply_text("Usage: <code>/takebalance &lt;amount&gt;</code> (Reply to user)", parse_mode=enums.ParseMode.HTML)
        return
    update_filter = get_user_id_query(recipient_id)
    update_filter["balance"] = {"$gte": amount}
    result = await user_collection.update_one(update_filter, {'$inc': {'balance': -amount, 'version': 1}})
    if result.modified_count == 0:
        await message.reply_text("User does not have enough balance to take that amount.")
        return
    await invalidate_user_cache(recipient_id)
    await message.reply_text(f"{amount} ⬪ taken from {html_escape(recipient.first_name)}!")
    LOGGER.info(f"ADMIN {sender_id} took {amount} from {recipient_id}")
