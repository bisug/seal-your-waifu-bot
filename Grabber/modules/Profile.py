from telegram.ext import CommandHandler
from Grabber import application, user_collection

async def my_profile(update, context):
    if update.message:
        user_id = update.effective_user.id

        # Retrieve user information from the database
        user_data = await user_collection.find_one({'id': user_id})

        if user_data:
            user_name = user_data.get('username', 'Unknown')
            user_id = user_data.get('id', 'Unknown')
            user_balance = user_data.get('balance', 0)
            characters_count = len(user_data.get('characters', []))

            # Set the profile picture URL
            profile_pic_url = "https://graph.org/file/3108f45cb5be50754666a.jpg"

            # Create a profile message with both the profile picture and other information
            profile_message = (
                f"User Profile:\n"
                f"Name: {user_name}\n"
                f"ID: {user_id}\n"
                f"Balance: 💵{user_balance} coins\n"
                f"Number of Characters: {characters_count}\n"
            )

            try:
                # Send the combined message with the photo and profile information
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=profile_pic_url, caption=profile_message)
            except Exception as e:
                print(f"Error in sending message: {e}")
        else:
            profile_message = "Unable to retrieve user information."

            try:
                await context.bot.send_message(chat_id=update.message.chat_id, text=profile_message)
            except Exception as e:
                print(f"Error in sending message: {e}")
    else:
        print("No message to reply to.")  # Optional: Print a message or log the issue

# Add the command handler to your application
application.add_handler(CommandHandler("myprofile", my_profile, block=False))
