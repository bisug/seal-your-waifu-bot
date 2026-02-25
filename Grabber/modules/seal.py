from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, OWNER_ID, sudo_users
from Grabber import group_user_totals_collection, LOGGER
from Grabber.core.user import add_char_to_user
from Grabber.core.spawns import get_chat_state, clear_active_spawn, get_message_count, send_character
from Grabber.core.progression import add_xp
from Grabber.modules.quests import update_quest_progress
from Grabber.modules.achievements import check_achievements
import random
import asyncio
from Grabber.modules.rarities import RARITY_WEIGHTS

AUTHORIZED_USERS = set(sudo_users + [OWNER_ID])

@app.on_message(filters.command("seal") & filters.group)
async def seal_handler(_, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
                              
    state = await get_chat_state(chat_id)
    character = state.get("last_character")
    
    if not character:
        return await message.reply_text("❌ There's no character to collect right now!")

    if state.get("first_correct_guess") is not None:
        return                 

    if len(message.command) < 2:
        return await message.reply_text("❌ Provide the character's name! Usage: <code>/seal &lt;name&gt;</code>", parse_mode=ParseMode.HTML)

    guess = " ".join(message.command[1:]).strip().lower()
    correct_name = character['name'].strip().lower()

    # guess name logic
    if guess == correct_name or any(part in guess for part in correct_name.split() if len(part) > 2):
        # Atomically try to claim the character
        if not await clear_active_spawn(chat_id, user_id):
            return # Someone else caught it already
        
        # Send one random big positive reaction
        async def send_reactions():
            try:
                # Using only standard reactions that are widely enabled
                emojis = ["🔥", "❤️", "🎉", "🤩", "👍", "🥰", "👏"]
                selected = random.choice(emojis)
                # Note: Some clients/forks use 'big', some use 'is_big', 
                # but if the error was REACTION_INVALID, it's the emoji itself.
                await app.send_reaction(chat_id, message_id=message.id, emoji=selected, big=True)
            except Exception as e:
                LOGGER.error(f"Failed to send reaction: {e}")

        asyncio.create_task(send_reactions())
        
                           
        await add_char_to_user(user_id, character)
        
                            
        await group_user_totals_collection.update_one(
            {"group_id": chat_id, "user_id": user_id},
            {"$inc": {"count": 1}},
            upsert=True
        )
        
                                    
        await add_xp(user_id, 10, "character_catch")
        await update_quest_progress(user_id, "catch_master", 1)
        await update_quest_progress(user_id, "weekly_catch", 1)

                            
        await check_achievements(user_id)

                      
        spawn_msg_id = state.get("message_id")
        if spawn_msg_id:
            try:
                await app.delete_messages(chat_id, spawn_msg_id)
            except:
                pass

        caption = (
            f"🎉 <b><a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a> caught the character!</b>\n\n"
            f"📛 <b>Name:</b> {html_escape(character['name'])}\n"
            f"✨ <b>Rarity:</b> {html_escape(character['rarity'])}\n"
            f"🎬 <b>Anime:</b> {html_escape(character['anime'])}\n"
            f"🧤 Added to your harem!"
        )
        
        await message.reply_photo(character['img_url'], caption=caption, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("❌ Wrong name! Try again.")

@app.on_message(filters.command("messagecount") & filters.group)
async def messagecount_handler(_, message: types.Message):
    count = await get_message_count(message.chat.id)
    await message.reply_text(f"📊 <b>Total messages in this chat:</b> <code>{count}</code>", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("cnow") & filters.group)
async def cnow_handler(_, message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return # Ignore non-owners
        
    weights_map = RARITY_WEIGHTS
    rarities = list(weights_map.keys())
    weights = list(weights_map.values())
    selected_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    await send_character(message.chat.id, selected_rarity)
