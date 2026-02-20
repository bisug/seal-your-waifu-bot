from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, user_collection, OWNER_ID, sudo_users, LOGGER
from Grabber.modules.quests import update_quest_progress
from Grabber.modules.achievements import check_achievements

                                                     
AUTHORIZED_ADMINS = set(sudo_users + [OWNER_ID])

@app.on_message(filters.command("givebalance"))
async def give_balance(_, message: types.Message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a user to give balance.")
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
        await message.reply_text("⚠️ Usage: <code>/givebalance &lt;amount&gt;</code> (Reply to user)", parse_mode=ParseMode.HTML)
        return

                                       
    if sender_id in AUTHORIZED_ADMINS:
        await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}}, upsert=True)
        await message.reply_text(f"✅ {amount} ⬪ given to {html_escape(recipient.first_name)}!")
        LOGGER.info(f"ADMIN {sender_id} gave {amount} to {recipient_id}")
        return

                        
    sender = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    sender_balance = sender.get("balance", 0) if sender else 0

    if sender_balance < amount:
        await message.reply_text("❌ Insufficient balance to give.")
        return

                 
    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}}, upsert=True)

    await message.reply_text(f"✅ You gave {amount} ⬪ to {html_escape(recipient.first_name)}!")
    LOGGER.info(f"User {sender_id} gave {amount} to {recipient_id}")
    
                  
    await update_quest_progress(sender_id, "generous_soul", 1)
    
                                                    
    await check_achievements(recipient_id)


@app.on_message(filters.command("takebalance"))
async def take_balance(_, message: types.Message):
    sender_id = message.from_user.id

    if sender_id not in AUTHORIZED_ADMINS:
        await message.reply_text("❌ You are not authorized to take balance.")
        return

    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a user to take balance from.")
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
        await message.reply_text("⚠️ Usage: <code>/takebalance &lt;amount&gt;</code> (Reply to user)", parse_mode=ParseMode.HTML)
        return

    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': -amount}})
    await message.reply_text(f"✅ {amount} ⬪ taken from {html_escape(recipient.first_name)}!")
    LOGGER.info(f"ADMIN {sender_id} took {amount} from {recipient_id}")
