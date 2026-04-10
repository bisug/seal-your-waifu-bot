from Grabber.core.utils import reply_media_dynamic
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, collection, user_collection, OWNER_ID, LOGGER

@app.on_message(filters.command("check"))
async def check_character(_, message: types.Message) -> None:
    try:
        if len(message.command) < 2:
            await message.reply_text('Incorrect format. Please use: <code>/check character_id</code>', parse_mode=ParseMode.HTML)
            return

        character_id = message.command[1]
        character = await collection.find_one({'id': character_id})

        if character:
            response_message = (
                f"<b>Character Name:</b> {html_escape(character['name'])}\n"
                f"<b>Anime:</b> {html_escape(character['anime'])}\n"
                f"<b>Rarity:</b> {html_escape(character['rarity'])}\n"
                f"<b>Character ID:</b> <code>{character['id']}</code>\n"
            )

            await reply_media_dynamic(message, character['img_url'],
                caption=response_message,
                parse_mode=ParseMode.HTML
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


    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return


    existing_user = await user_collection.find_one({'id': user_id, 'characters.id': character_id})
    if existing_user:
        await message.reply_text(f'You already have {character["name"]} in your harem!')
        return


    await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    await message.reply_text(f'Character {character["name"]} added to your harem!')
