import asyncio
import os
import re

from pyrogram import enums, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import (GALLERY_CHANNEL_ID, LOGGER, OWNER_ID, app, collection,
                     sudo_users, userbot)
from Grabber.core.utils import send_media_dynamic
from Grabber.core.waifu import (add_character_to_db,
                                invalidate_character_cache,
                                upload_media_safely)
from Grabber.modules.collection.rarities import RARITY_MAP

# Hardcoded Review Group
LOG_GROUP_ID = config.LOG_GROUP_ID

# Global state to manage active scraping tasks
scraping_tasks = {}

def clean_text(text: str) -> str:
    """Cleans text of brackets, counts, emojis, and extra whitespace."""
    if not text: return ""
    # Remove bracket items like [🎒] or [x1]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove count items like (x1) or (1/89)
    text = re.sub(r'\(x\d+\)', '', text, flags=re.I)
    text = re.sub(r'\(\d+/\d+\)', '', text)
    # Preserve only normal text, numbers, spaces, and acceptable characters 
    # instead of strictly purging all non-ascii, which drops certain formats.
    text = re.sub(r'[^\w\s\-\'\.]+', '', text)
    return text.strip()

def smart_parse_character(text: str):
    """
    Parses various character message formats using regex spanning 7+ formats.
    Returns (name, anime) or (None, None).
    """
    if not text: return None, None
    
    patterns = [
        # Format: 🌸 Hakari Hanazono \n ... 🏖️ From: The 100 Girlfriends ...
        (r'🌸\s*(?P<name>[^\n]+)\n.*?From:\s*(?P<anime>[^\n]+)', re.I | re.S),
        
        # Format: Name: Sabo ... Anime: One Piece
        (r'(?:\*Name\*|Name|NAME|Character):\s*(?P<name>[^\n]+)\n.*?(?:\*Anime\*|Anime|ANIME|Series|From|FROM):\s*(?P<anime>[^\n]+)', re.I | re.S),
        
        # Format: 1804: Mikasa Ackerman \n Attack On Titan \n ʀᴀʀɪᴛʏ:
        (r'(?:^|\n)\d+:\s*(?P<name>[^\n]+)\n(?P<anime>[^\n]+)\n.*?ʀᴀʀɪᴛʏ:', re.I | re.S),

        # Format: Anime\n 1234: Name
        (r'(?:^|\n)(?P<anime>[^\n]+)\n\d+:\s*(?P<name>[^\n]+)', re.I),
        
        # Format: Augusta [🎒] \n Anime: Wuthering Waves
        (r'(?:^|\n)(?P<name>[^\n]+?)\s*(?:\[.*?\])?\s*\n+(?:Anime|ANIME):\s*(?P<anime>[^\n]+)', re.I),
    ]

    for pattern, flags in patterns:
        match = re.search(pattern, text, flags=flags)
        if match:
            name = clean_text(match.group('name'))
            anime = clean_text(match.group('anime'))
            
            # Additional safety: ensure it's on a single line
            anime = anime.split('\n')[0].strip()
            
            if name and anime:
                return name, anime

    return None, None

def get_review_keyboard():
    """Buttons for selecting rarity or declining a character."""
    buttons = []
    # Rarity Choices (Dynamic based on RARITY_MAP)
    row = []
    for i in sorted(RARITY_MAP.keys()):
        rarity_full = RARITY_MAP[i]
        # Extract name part: "🟢 Medium" -> "Medium"
        rarity_name = rarity_full.split(" ", 1)[1] if " " in rarity_full else rarity_full
        row.append(types.InlineKeyboardButton(rarity_name, callback_data=f"rsc_app:{i}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    buttons.append([types.InlineKeyboardButton("❌ Decline", callback_data="rsc_dec")])
    return types.InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("scrape") & filters.user(sudo_users + [OWNER_ID]))
async def scrape_group_command_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/scrape <group_id_or_username>`\nNote: Bot must be a member of the group.")

    if message.chat.id in scraping_tasks:
        return await message.reply_text("⚠️ A scraping task is already running. Use `/stop_scrape`.")

    target_chat = message.command[1]
    status = await message.reply_text(f"⏳ Scanning `{target_chat}` for characters...")

    try:
        # Use userbot for scraping if available, otherwise fallback to app
        client_to_use = userbot if userbot and userbot.is_connected else app
        is_userbot = (client_to_use == userbot)

        # Resolve chat
        try:
            chat = await client_to_use.get_chat(target_chat)
        except Exception as e:
            error_tip = "Make sure Bot is added." if not is_userbot else "Make sure UserBot is a member."
            return await status.edit_text(f"❌ Could not access chat: {e}\n{error_tip}")

        scraping_tasks[message.chat.id] = True
        sent_count = 0
        
        # Iterate backwards through history
        async for msg in client_to_use.get_chat_history(chat.id, limit=300):
            if message.chat.id not in scraping_tasks:
                break

            # Process only photos or docs (media)
            if not (msg.photo or msg.document):
                continue

            caption = msg.caption or msg.text
            name, anime = smart_parse_character(caption)

            if not name or not anime:
                continue

            # Check if exists locally
            exists = await collection.find_one({"name": name, "anime": anime})
            if exists:
                continue

            try:
                # Send for Review
                # We download first to ensure we have a valid file to re-upload to our group
                temp_path = await client_to_use.download_media(msg)
                
                review_caption = (
                    f"<b>🆕 Scraped Character!</b>\n\n"
                    f"👤 <b>Name:</b> {name}\n"
                    f"🎬 <b>Anime:</b> {anime}\n\n"
                    "Select Rarity to Approve or Decline below:"
                )

                await send_media_dynamic(app, chat_id=LOG_GROUP_ID, media_url=temp_path,
                    caption=review_caption,
                    reply_markup=get_review_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                
                if os.path.exists(temp_path): os.remove(temp_path)
                
                sent_count += 1
                await asyncio.sleep(2)

                if sent_count >= 15: # Batch limit
                    await message.reply_text(f"✅ Batch of {sent_count} characters sent to review group. Run `/scrape` again for more.")
                    break

            except Exception as e:
                LOGGER.error(f"Scrape Error: {e}")
                continue

        if message.chat.id in scraping_tasks:
            del scraping_tasks[message.chat.id]
            if sent_count == 0:
                await message.reply_text("✅ Scraping complete. No new characters found.")
            elif sent_count < 15:
                await message.reply_text(f"✅ Scraping complete. Sent {sent_count} characters.")

    except Exception as e:
        LOGGER.error(f"Scraper Failed: {e}")
        if message.chat.id in scraping_tasks: del scraping_tasks[message.chat.id]
        await status.edit_text(f"❌ Scraper Failed: {e}")

@app.on_message(filters.command("stop_scrape") & filters.user(sudo_users + [OWNER_ID]))
async def stop_scrape_handler(client, message):
    if message.chat.id in scraping_tasks:
        del scraping_tasks[message.chat.id]
        await message.reply_text("🛑 Scraper task stopped.")
    else:
        await message.reply_text("ℹ️ No active scraper task.")

@app.on_callback_query(filters.regex(r"^rsc_app:(\d+)$"))
async def approve_scrape_callback(client, query):
    if query.from_user.id not in (sudo_users + [OWNER_ID]):
        return await query.answer("❌ Admin only.")

    rarity_num = int(query.data.split(":")[1])
    
    # Parse info from caption using regex — resilient to caption format changes
    caption = query.message.caption or ""
    # Look for Name/Anime or Name/Series or Character/Anime pattern
    name_match = re.search(r"(?:Name|Character):\s*(.+)", caption, re.I)
    anime_match = re.search(r"(?:Anime|Series):\s*(.+)", caption, re.I)
    
    if not name_match or not anime_match:
        # Fallback to lines if regex fails
        lines = caption.split("\n")
        name, anime = None, None
        for line in lines:
            if "Name:" in line or "Character:" in line:
                name = line.split(":", 1)[1].strip()
            if "Anime:" in line or "Series:" in line:
                anime = line.split(":", 1)[1].strip()
        
        if not name or not anime:
            return await query.answer("❌ Error parsing metadata.")
    else:
        name = name_match.group(1).strip()
        anime = anime_match.group(1).strip()

    await query.answer("♻️ Re-hosting & Integrating...")
    await query.message.edit_reply_markup(None)

    status_msg = await query.message.reply_text("📥 Re-hosting to Catbox...")

    try:
        # Download from our own review group
        temp_path = await app.download_media(query.message.photo.file_id)
        final_url = await upload_media_safely(temp_path)
        
        if not final_url:
            return await status_msg.edit_text("❌ Re-hosting failed.")

        rarity_text = RARITY_MAP[rarity_num]
        invalidate_character_cache(rarity_text)
        
        # Post to Channel
        channel_caption = (
            f"<b>Character Name:</b> {name}\n"
            f"<b>Anime Name:</b> {anime}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"<i>Approved by Admin</i>"
        )
        
        sent_msg = await send_media_dynamic(app, chat_id=GALLERY_CHANNEL_ID, media_url=final_url,
            caption=channel_caption,
            parse_mode=ParseMode.HTML
        )

        # DB Save
        char_data = {
            'img_url': final_url,
            'name': name,
            'anime': anime,
            'rarity': rarity_text,
            'message_id': sent_msg.id if sent_msg else None
        }
        
        char_id = await add_character_to_db(char_data)
        
        await status_msg.edit_text(f"✅ <b>Integrated!</b>\nName: {name}\nID: <code>{char_id}</code>")
        await query.message.delete()

    except Exception as e:
        LOGGER.error(f"Approval Error: {e}")
        await status_msg.edit_text(f"❌ Error: {e}")

@app.on_callback_query(filters.regex(r"^rsc_dec$"))
async def decline_scrape_callback(client, query):
    if query.from_user.id not in (sudo_users + [OWNER_ID]):
        return await query.answer("❌ Admin only.")
    await query.answer("❌ Declined.")
    await query.message.delete()
