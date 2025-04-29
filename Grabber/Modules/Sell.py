from pyrogram import Client, filters
from Grabber import Grabberu as app
from Grabber import user_collection

@app.on_message(filters.command("tops") & filters.private)
async def leaderboard(client, message):
    # Fetch users from the database (await cursor conversion)
    cursor = user_collection.find({}, {"_id": 0, "username": 1, "first_name": 1, "characters": 1})
    leaderboard_data = await cursor.to_list(length=None)  # ✅ Use await to convert cursor to list
    leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)  # Sort by character count
    leaderboard_data = leaderboard_data[:10]  # Get top 10 users

    # Prepare leaderboard message
    leaderboard_message = "<b>🏆 Top 10 Users with Most Characters 🏆</b>\n\n"

    print("\n🔹 Top 10 Users (Console Log):")  # Print header in console

    for i, user in enumerate(leaderboard_data, start=1):
        first_name = user.get('first_name', 'Unknown')
        first_name = (first_name[:15] + '...') if len(first_name) > 15 else first_name  # Truncate long names
        character_count = len(user.get('characters', []))

        leaderboard_message += f"{i}. <b>{first_name}</b> ➾ <b>{character_count} Characters</b>\n"

        # Print each user in the console
        print(f"{i}. {first_name} ➾ {character_count} Characters")

    # Send leaderboard as a text message
    await message.reply_text(leaderboard_message, parse_mode="HTML")
    
