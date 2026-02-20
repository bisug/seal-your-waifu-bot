import random
import re
import asyncio
from pyrogram import filters, types, errors
from pyrogram.enums import ParseMode
from pymongo import ReturnDocument
from Grabber import app
from Grabber import collection, user_collection, sessions_collection, nguess_enabled_groups_collection, LOGGER, OWNER_ID
from Grabber.core.game import update_user_balance

# Local cache is no longer used for character data to ensure persistence
# Active sessions are stored in sessions_collection with ID: "nguess:{chat_id}"

from Grabber.core.utils import md_escape as escape_markdown_v2

async def delete_after(message, delay: int):
    """Wait for delay seconds and then delete the message."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

async def send_message_safe(chat_id, text=None, photo=None, caption=None, parse_mode=ParseMode.MARKDOWN, reply_markup=None, auto_delete=False):
    """Sends a message or photo while handling FloodWait professionally."""
    try:
        if photo:
            msg = await app.send_photo(chat_id, photo, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            msg = await app.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
        
        if msg and auto_delete:
            asyncio.create_task(delete_after(msg, 300)) # 5 minutes
        return msg
    except errors.FloodWait as e:
        LOGGER.warning(f"FloodWait detected: Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value)
        return await send_message_safe(chat_id, text, photo, caption, parse_mode, reply_markup, auto_delete)
    except Exception as e:
        LOGGER.error(f"Error in send_message_safe: {e}")
        return None

def get_name_variants(name: str):
    """Generates possible name variants for matching."""
    name = name.lower().strip()
    parts = re.split(r'\s+', name)
    variants = {name}
    for part in parts:
        if len(part) > 2:
            variants.add(part)
    return variants

@app.on_message(filters.command("nguess"))
async def nguess_start_handler(_, message: types.Message):
    chat_id = message.chat.id
    
    # Check if group is enabled
    is_enabled = await nguess_enabled_groups_collection.find_one({"chat_id": chat_id})
    if not is_enabled and chat_id not in [OWNER_ID]:
        return
    
    # Check if a game is already active in DB
    existing_session = await sessions_collection.find_one({"_id": f"nguess:{chat_id}"})
    if existing_session:
        return await send_message_safe(chat_id, text=escape_markdown_v2("ONGOING MISSION\nAn identification request is already active in this sector."), auto_delete=True)

    # Fetch a random character
    cursor = collection.aggregate([{"$sample": {"size": 1}}])
    res = await cursor.to_list(length=1)
    if not res:
        return await send_message_safe(chat_id, text=escape_markdown_v2("DATABASE ERROR: No target profiles available."), auto_delete=True)
    
    char = res[0]
    
    # Create session in DB
    await sessions_collection.insert_one({
        "_id": f"nguess:{chat_id}",
        "char": char,
        "players": []
    })

    anime_name = escape_markdown_v2(char['anime'])
    briefing = (
        "**IDENTIFY THE TARGET**\n\n"
        f"**Origin:** {anime_name}\n"
        "**Rarity:** Classified\n\n"
        "**Instruction:** Type the name in chat to win shards"
    )
    
    sent = await send_message_safe(
        chat_id,
        photo=char['img_url'],
        caption=briefing,
        auto_delete=True
    )
    
    if not sent:
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}"})
        await send_message_safe(chat_id, text=escape_markdown_v2("CRITICAL FAILURE: Transponder link lost."), auto_delete=True)

@app.on_message(filters.command("ngon") & filters.user(OWNER_ID))
async def ngon_handler(_, message: types.Message):
    try:
        args = message.text.split()
        chat_id = int(args[1]) if len(args) > 1 else message.chat.id
        
        await nguess_enabled_groups_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": True}},
            upsert=True
        )
        msg_text = escape_markdown_v2(f"SECTOR AUTHORIZED: /nguess is now active for sector {chat_id}.")
        await send_message_safe(message.chat.id, text=msg_text, auto_delete=True)
    except ValueError:
        await send_message_safe(message.chat.id, text=escape_markdown_v2("ERROR: Invalid Chat ID format."), auto_delete=True)

@app.on_message(filters.command("ngoff") & filters.user(OWNER_ID))
async def ngoff_handler(_, message: types.Message):
    try:
        args = message.text.split()
        chat_id = int(args[1]) if len(args) > 1 else message.chat.id
        
        await nguess_enabled_groups_collection.delete_one({"chat_id": chat_id})
        msg_text = escape_markdown_v2(f"AUTHORIZATION REVOKED: /nguess is now disabled for sector {chat_id}.")
        await send_message_safe(message.chat.id, text=msg_text, auto_delete=True)
    except ValueError:
        await send_message_safe(message.chat.id, text=escape_markdown_v2("ERROR: Invalid Chat ID format."), auto_delete=True)

@app.on_message(filters.command("nglist") & filters.user(OWNER_ID))
async def nglist_handler(_, message: types.Message):
    enabled_groups = await nguess_enabled_groups_collection.find().to_list(length=100)
    if not enabled_groups:
        return await send_message_safe(message.chat.id, text=escape_markdown_v2("REGISTRY EMPTY: No sectors are currently authorized."), auto_delete=True)
    
    text = "**AUTHORIZED SECTORS FOR /NGUESS**\n\n"
    for group in enabled_groups:
        text += f"• `{group['chat_id']}`\n"
    
    await send_message_safe(message.chat.id, text=text, auto_delete=True)

@app.on_message(filters.text & filters.group & ~filters.command(["nguess", "top", "ctop"]), group=10)
async def nguess_check_handler(_, message: types.Message):
    chat_id = message.chat.id
    
    # Update player list atomically
    session = await sessions_collection.find_one_and_update(
        {"_id": f"nguess:{chat_id}"},
        {"$addToSet": {"players": message.from_user.id}},
        return_document=ReturnDocument.AFTER
    )
    
    if not session:
        return

    guess = message.text.lower().strip()
    char = session["char"]
    name_variants = get_name_variants(char['name'])
    
    if guess in name_variants:
        # Correct guess!
        player_count = len(session.get("players", []))
        reward = min(10 + (player_count - 1) * 5, 50)
        
        # Increment global counter
        stats = await sessions_collection.find_one_and_update(
            {"id": "nguess_global_stats"},
            {"$inc": {"total_guesses": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        total_guesses = stats.get("total_guesses", 1)
        
        bonus = 0
        milestone_text = ""
        
        if total_guesses % 100 == 0:
            bonus = 1000
            milestone_text = escape_markdown_v2(f"\n\n**ELITE MILESTONE ACHIEVED**\nYou are the 100th guesser! Granted 1,000 bonus Shards.")
            await sessions_collection.update_one({"id": "nguess_global_stats"}, {"$set": {"total_guesses": 0}})
        elif total_guesses % 100 == 50:
            bonus = 500
            milestone_text = escape_markdown_v2(f"\n\n**MILESTONE REACHED**\nYou are the 50th guesser! Granted 500 bonus Shards.")

        total_reward = reward + bonus
        
        # Update user
        await user_collection.update_one(
            {"id": message.from_user.id},
            {
                "$inc": {"balance": total_reward, "guess_count": 1},
                "$setOnInsert": {"first_name": message.from_user.first_name}
            },
            upsert=True
        )
        
        # Delete session
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}"})
        
        display_progress = total_guesses % 100 if total_guesses % 100 != 0 else 100
        
        mention = message.from_user.mention
        target_name = escape_markdown_v2(char['name'])
        
        success_msg = (
            f"**TARGET IDENTIFIED**\n\n"
            f"**Agent:** {mention}\n"
            f"**Name:** {target_name}\n"
            f"**Bounty:** {reward} Shards\n"
            f"**Progress:** {display_progress}/100{milestone_text}"
        )
        
        await send_message_safe(chat_id, text=success_msg, auto_delete=True)
    else:
        # Silently ignore wrong guesses
        pass
