
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, user_totals_collection, LOGGER

@app.on_message(filters.command("changetime") & filters.group)
async def change_time(_, message: types.Message) -> None:
    user = message.from_user
    chat = message.chat

    try:
                                                    
        member = await app.get_chat_member(chat.id, user.id)
        if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
            await message.reply_text('You do not have permission to use this command.')
            return

        if len(message.command) != 2:
            await message.reply_text('Incorrect format. Please use: `/changetime <number>`', parse_mode=ParseMode.MARKDOWN_V2)
            return

        try:
            new_frequency = int(message.command[1])
        except ValueError:
            await message.reply_text('Please provide a valid number.')
            return

        if new_frequency < 50:                                                
            await message.reply_text('The message frequency must be at least 50.')
            return
        
        if new_frequency > 10000:
            await message.reply_text('That\'s too much buddy. Use below 10000.')
            return

        await user_totals_collection.find_one_and_update(
            {'chat_id': str(chat.id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=True
        )

        await message.reply_text(f'Successfully changed character appearance frequency to every {new_frequency} messages.')
    except Exception as e:
        LOGGER.error(f"Error in changetime: {e}")
        await message.reply_text('Failed to change character appearance frequency.')
