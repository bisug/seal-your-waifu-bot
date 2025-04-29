from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Grabber import user_collection, Grabberu

pending_trades = {}
pending_gifts = {}

@Grabberu.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to trade a character!")
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text("You can't trade a character with yourself!")
        return

    if len(message.command) != 3:
        await message.reply_text("You need to provide two character IDs!")
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    if not sender or not receiver:
        await message.reply_text("One of the users does not exist in the database.")
        return

    sender_character = next(
        (char for char in sender.get('characters', []) if isinstance(char, dict) and char.get('id') == sender_character_id), None)
    receiver_character = next(
        (char for char in receiver.get('characters', []) if isinstance(char, dict) and char.get('id') == receiver_character_id), None)

    if not sender_character:
        await message.reply_text("You don't have the character you're trying to trade!")
        return

    if not receiver_character:
        await message.reply_text("The other user doesn't have the character they're trying to trade!")
        return

    pending_trades[(sender_id, receiver_id)] = (sender_character_id, receiver_character_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Trade", callback_data=f"confirm_trade:{sender_id}:{receiver_id}")],
        [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_trade:{sender_id}:{receiver_id}")]
    ])

    await message.reply_text(
        f"{message.reply_to_message.from_user.mention}, do you accept this trade?",
        reply_markup=keyboard
    )


@Grabberu.on_callback_query(filters.regex(r"^(confirm_trade|cancel_trade):(\d+):(\d+)$"))
async def on_trade_callback(client, callback_query):
    action, sender_id, receiver_id = callback_query.data.split(":")
    sender_id, receiver_id = int(sender_id), int(receiver_id)

    if callback_query.from_user.id != receiver_id:
        await callback_query.answer("⚠️ This trade request is not for you!", show_alert=True)
        return

    if (sender_id, receiver_id) not in pending_trades:
        await callback_query.answer("⚠️ No active trade request found!", show_alert=True)
        return

    if action == "confirm_trade":
        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        sender_character_id, receiver_character_id = pending_trades[(sender_id, receiver_id)]

        sender_character = next(
            (char for char in sender.get('characters', []) if isinstance(char, dict) and char.get('id') == sender_character_id), None)
        receiver_character = next(
            (char for char in receiver.get('characters', []) if isinstance(char, dict) and char.get('id') == receiver_character_id), None)

        if not sender_character or not receiver_character:
            await callback_query.message.edit_text("⚠️ One of the characters is missing!")
            return

        sender['characters'].remove(sender_character)
        receiver['characters'].remove(receiver_character)

        sender['characters'].append(receiver_character)
        receiver['characters'].append(sender_character)

        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver['characters']}})

        del pending_trades[(sender_id, receiver_id)]

        await callback_query.message.edit_text(f"✅ Trade successful!")
    else:
        del pending_trades[(sender_id, receiver_id)]
        await callback_query.message.edit_text("❌ Trade canceled.")
        pending_gifts = {}

@Grabberu.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to gift a character!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text("You can't gift a character to yourself!")
        return

    if len(message.command) != 2:
        await message.reply_text("You need to provide a character ID!")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})
    if not sender:
        await message.reply_text("⚠️ You don't have any characters in your collection!")
        return

    sender_character = next(
        (char for char in sender.get('characters', []) if isinstance(char, dict) and char.get('id') == character_id), None)

    if not sender_character:
        await message.reply_text("⚠️ You don't have this character in your collection!")
        return

    pending_gifts[sender_id] = {
        'character': sender_character,
        'receiver_id': receiver_id,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Confirm Gift", callback_data=f"confirm_gift:{sender_id}")],
        [InlineKeyboardButton("❌ Cancel Gift", callback_data=f"cancel_gift:{sender_id}")]
    ])

    await message.reply_text(
        f"🎁 Are you sure you want to gift {sender_character['name']} to {message.reply_to_message.from_user.mention}?",
        reply_markup=keyboard
    )


@Grabberu.on_callback_query(filters.regex(r"^(confirm_gift|cancel_gift):(\d+)$"))
async def on_gift_callback(client, callback_query):
    action, sender_id = callback_query.data.split(":")
    sender_id = int(sender_id)

    if callback_query.from_user.id != sender_id:
        await callback_query.answer("⚠️ This is not for you!", show_alert=True)
        return

    if sender_id not in pending_gifts:
        await callback_query.answer("⚠️ No active gift request found!", show_alert=True)
        return

    if action == "confirm_gift":
        gift = pending_gifts.pop(sender_id)

        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': gift['receiver_id']})

        if not sender or not gift['character'] in sender['characters']:
            await callback_query.message.edit_text("gift successfully")
            return

        sender['characters'] = [c for c in sender['characters'] if c != gift['character']]
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})

        if receiver:
            await user_collection.update_one({'id': gift['receiver_id']}, {'$push': {'characters': gift['character']}})
        else:
            await user_collection.insert_one({
                'id': gift['receiver_id'],
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'characters': [gift['character']],
            })

        await callback_query.message.edit_text(f"🎁 Gift sent successfully!")
    else:
        del pending_gifts[sender_id]
        await callback_query.message.edit_text("❌ Gift canceled.")
        
