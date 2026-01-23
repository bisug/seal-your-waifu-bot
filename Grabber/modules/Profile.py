from pyrogram import filters, types, enums
from Grabber import app, user_collection, PHOTO_URL, LOGGER

@app.on_message(filters.command("myprofile"))
async def my_profile(_, message: types.Message):
    user_id = message.from_user.id

    # Retrieve user information from the database
    user_data = await user_collection.find_one({'id': user_id})

    if user_data:
        user_name = message.from_user.first_name
        user_balance = user_data.get('balance', 0)
        characters_count = len(user_data.get('characters', []))

        # Set the profile picture URL from config
        profile_pic_url = PHOTO_URL[0]

        # Create a profile message
        profile_message = (
            f"**👤 User Profile**\n\n"
            f"📛 **Name:** {user_name}\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"💵 **Balance:** {user_balance} coins\n"
            f"🎒 **Characters:** {characters_count}\n"
        )

        try:
            await message.reply_photo(photo=profile_pic_url, caption=profile_message, parse_mode=enums.ParseMode.MARKDOWN)
        except Exception as e:
            LOGGER.error(f"Error in sending Profile message: {e}")
            await message.reply_text(profile_message, parse_mode=enums.ParseMode.MARKDOWN)
    else:
        await message.reply_text("🚨 No profile found! Try collecting a character first.")
