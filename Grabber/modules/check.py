from pyrogram import filters, types, enums
from Grabber import app, collection, user_collection, OWNER_ID, LOGGER

@app.on_message(filters.command("check"))
async def check_character(_, message: types.Message) -> None:
    try:
        if len(message.command) < 2:
            await message.reply_text('Incorrect format. Please use: `/check character_id`', parse_mode=enums.ParseMode.MARKDOWN)
            return

        character_id = message.command[1]
        character = await collection.find_one({'id': character_id})

        if character:
            response_message = (
                f"**Character Name:** {character['name']}\n"
                f"**Anime:** {character['anime']}\n"
                f"**Rarity:** {character['rarity']}\n"
                f"**Character ID:** `{character['id']}`\n"
            )

            await message.reply_photo(
                photo=character['img_url'],
                caption=response_message,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await message.reply_text('Character not found.')

    except Exception as e:
        LOGGER.error(f"Error in check_character: {e}")
        await message.reply_text(f'Error: {str(e)}')

@app.on_message(filters.command("give") & filters.user(OWNER_ID))
async def give_cmd(_, message: types.Message) -> None:
    user_id = message.from_user.id

    if len(message.command) < 2:
        await message.reply_text('Please provide a Character ID...')
        return

    character_id = message.command[1]

    # Retrieve character from the collection based on the provided ID
    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    # Check if the user already has the character in their harem
    existing_user = await user_collection.find_one({'id': user_id, 'characters.id': character_id})
    if existing_user:
        await message.reply_text(f'You already have {character["name"]} in your harem!')
        return

    # Update the user's harem with the character
    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    await message.reply_text(f'Character {character["name"]} added to your harem!')
