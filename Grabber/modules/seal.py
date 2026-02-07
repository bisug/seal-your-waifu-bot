from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import group_user_totals_collection, LOGGER
from Grabber.core.user import add_char_to_user
from Grabber.core.spawns import get_chat_state, clear_active_spawn, get_message_count
from Grabber.core.progression import add_xp
from Grabber.modules.quests import update_quest_progress
from Grabber.modules.achievements import check_achievements

@app.on_message(filters.command("seal") & filters.group)
async def seal_handler(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Fetch state from MongoDB
    state = await get_chat_state(chat_id)
    character = state.get("last_character")
    
    if not character:
        return await message.reply_text("❌ There's no character to collect right now!")

    if state.get("first_correct_guess") is not None:
        return # Already caught

    if len(message.command) < 2:
        return await message.reply_text("❌ Provide the character's name! Usage: `/seal <name>`", parse_mode=enums.ParseMode.MARKDOWN)

    guess = " ".join(message.command[1:]).strip().lower()
    correct_name = character['name'].strip().lower()

    # Match logic
    if guess == correct_name or any(part in guess for part in correct_name.split() if len(part) > 2):
        # Atomic capture in MongoDB logic (simulation here with state check)
        # In a real high-load scenario, we'd use a conditional update $set: {guess: uid} if guess: None
        await clear_active_spawn(chat_id, user_id)
        
        # Add to collection
        await add_char_to_user(user_id, character)
        
        # Update group stats
        await group_user_totals_collection.update_one(
            {"group_id": chat_id, "user_id": user_id},
            {"$inc": {"count": 1}},
            upsert=True
        )
        
        # Grant XP and update quests
        await add_xp(user_id, 10, "character_catch")
        await update_quest_progress(user_id, "catch_master", 1)
        await update_quest_progress(user_id, "weekly_catch", 1)

        # Check Achievements
        await check_achievements(user_id)

        # UI Responses
        spawn_msg_id = state.get("message_id")
        if spawn_msg_id:
            try:
                await app.delete_messages(chat_id, spawn_msg_id)
            except:
                pass

        caption = (
            f"🎉 **[{message.from_user.first_name}](tg://user?id={message.from_user.id}) caught the character!**\n\n"
            f"📛 **Name:** {character['name']}\n"
            f"✨ **Rarity:** {character['rarity']}\n"
            f"🎬 **Anime:** {character['anime']}\n"
            f"🧤 Added to your harem!"
        )
        
        await message.reply_photo(character['img_url'], caption=caption)
    else:
        await message.reply_text("❌ Wrong name! Try again.")

@app.on_message(filters.command("messagecount") & filters.group)
async def messagecount_handler(_, message: types.Message):
    count = await get_message_count(message.chat.id)
    await message.reply_text(f"📊 **Total messages in this chat:** `{count}`")
