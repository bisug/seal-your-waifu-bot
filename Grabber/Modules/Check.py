import urllib.request
import os
from pymongo import ReturnDocument

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from Grabber import application, sudo_users, collection, db, CHARA_CHANNEL_ID

async def check_character(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check character_id')
            return

        character_id = args[0]
        character = await collection.find_one({'id': character_id})

        if character:
            response_message = (
                f"Character Name: {character['name']}\n"
                f"Anime: {character['anime']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Character ID: {character['id']}\n"
            )

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=character['img_url'],
                caption=response_message
            )
        else:
            await update.message.reply_text('Character not found.')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# ... (Previous code remains unchanged)

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import collection, user_collection, application

# Set the owner's user ID
OWNER_ID = 5932230962  # Replace with the actual owner's user ID

async def give(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is the owner
    if user_id != OWNER_ID:
        await update.message.reply_text('You are not authorized to use this command.')
        return

    if not context.args:
        await update.message.reply_text('Please provide a Character ID...')
        return

    character_id = context.args[0]

    # Retrieve character from the collection based on the provided ID
    character = await collection.find_one({'id': character_id})
    if not character:
        await update.message.reply_text('Character not found.')
        return

    # Check if the user already has the character in their harem
    existing_user = await user_collection.find_one({'id': user_id, 'characters.id': character_id})
    if existing_user:
        await update.message.reply_text(f'You already have {character["name"]} in your harem!')
        return

    # Update the user's harem with the character
    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    await update.message.reply_text(f'Character {character["name"]} added to your harem!')

# Inside main(), add this line to register the /give command handler
application.add_handler(CommandHandler("give", give, block=False))

CHECK_HANDLER = CommandHandler('check', check_character, block=False)
application.add_handler(CHECK_HANDLER)
