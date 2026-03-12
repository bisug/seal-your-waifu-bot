import re
import asyncio
import os
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, collection, OWNER_ID, CHARA_CHANNEL_ID, LOGGER, userbot
from Grabber.core.waifu import upload_image_to_catbox, add_character_to_db
from Grabber.modules.collection.rarities import RARITY_MAP
from config import config

# Hardcoded Review Group
REVIEW_GROUP_ID = -1002767033399

# Global state to manage active scraping tasks
scraping_tasks = {}

def clean_text(text: str) -> str:
    """Cleans text of brackets, emojis, and extra whitespace."""
    if not text: return ""
    text = re.sub(r'\[.*?\]', '', text)
    # Remove emojis and special characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()

def smart_parse_character(text: str):
    """
    Parses various character message formats using regex.
    Returns (name, anime) or (None, None).
    """
    if not text: return None, None
    
    patterns = [
        # Format 1: 🌸 Hakari Hanazono ... 🏖️ From: The 100 Girlfriends ...
        (r"🌸\s*(?P<name>.*?)\n.*?From:\s*(?P<anime>.*)", re.S),
        # Format 3 & 7: 🧩 *Name*: Nico Robin ... 📺 *Anime*: One Piece
        (r"(?:\*Name\*|Name):\s*(?P<name>.*?)\n.*?(?:\*Anime\*|Anime|From):\s*(?P<anime>.*)", re.I | re.S),
        # Format 4: 📛 Name: Sabo ... 📺 Anime: One Piece
        (r"📛\s*Name:\s*(?P<name>.*?)\n.*?📺\s*Anime:\s*(?P<anime>.*)", re.I | re.S),
        # Format 5: - NAME: Fubuki ... - FROM: One Punch Man
        (r"NAME:\s*(?P<name>.*?)\n.*?FROM:\s*(?P<anime>.*)", re.I | re.S),
        # Format 2 & 6: 12790: Ryuuge Kisaki [👶] ... (Line above usually Anime)
        # We'll try to get the line before the ID
        (r"(?P<anime>.*?)\n\d+:\s*(?P<name>.*?)(?:\n|\(|$)", re.S),
    ]

    for pattern, flags in patterns:
        match = re.search(pattern, text, flags=flags)
        if match:
            name = clean_text(match.group("name"))
            anime = clean_text(match.group("anime"))
            # Extra cleanup: sometimes anime gets lines after it
            anime = anime.split("\n")[0].strip()
            if name and anime:
                return name, anime

    return None, None

def get_review_keyboard(char_info: dict):
    """Buttons for selecting rarity or declining a character."""
    buttons = []
    # Rarity Choices (1-10)
    row = []
    for i in range(1, 11):
        rarity_full = RARITY_MAP.get(i, "Unknown")
        rarity_name = rarity_full.split(" ")[1] if " " in rarity_full else rarity_full
        row.append(types.InlineKeyboardButton(rarity_name, callback_data=f"rsc_app:{i}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    buttons.append([types.InlineKeyboardButton("❌ Decline", callback_data="rsc_dec")])
    return types.InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("scrape") & filters.user(OWNER_ID))
async def scrape_group_command_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/scrape <group_id_or_username>`")

    if not userbot:
        return await message.reply_text("❌ Userbot is not configured/started. Add `STRING_SESSION` to config.")

    if message.chat.id in scraping_tasks:
        return await message.reply_text("⚠️ A scraping task is already running. Use `/stop_scrape`.")

    target_chat = message.command[1]
    status = await message.reply_text(f"⏳ Scanning `{target_chat}` for characters...")

    try:
        # Resolve chat
        try:
            chat = await userbot.get_chat(target_chat)
        except Exception as e:
            return await status.edit_text(f"❌ Could not access chat: {e}")

        scraping_tasks[message.chat.id] = True
        sent_count = 0
        
        # Iterate backwards through history
        async for msg in userbot.get_chat_history(chat.id, limit=300):
            if message.chat.id not in scraping_tasks:
                break

            # Process only photos or docs that might be characters
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
                # We download and re-upload because Bot can't use Userbot's File IDs reliably across chats
                temp_path = await userbot.download_media(msg)
                
                review_caption = (
                    f"<b>🆕 Scraped Character!</b>\n\n"
                    f"👤 <b>Name:</b> {name}\n"
                    f"🎬 <b>Anime:</b> {anime}\n\n"
                    "Select Rarity to Approve or Decline below:"
                )

                await app.send_photo(
                    chat_id=REVIEW_GROUP_ID,
                    photo=temp_path,
                    caption=review_caption,
                    reply_markup=get_review_keyboard({}),
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

@app.on_message(filters.command("stop_scrape") & filters.user(OWNER_ID))
async def stop_scrape_handler(client, message):
    if message.chat.id in scraping_tasks:
        del scraping_tasks[message.chat.id]
        await message.reply_text("🛑 Scraper task stopped.")
    else:
        await message.reply_text("ℹ️ No active scraper task.")

@app.on_callback_query(filters.regex(r"^rsc_app:(\d+)$"))
async def approve_scrape_callback(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Admin only.")

    rarity_num = int(query.data.split(":")[1])
    
    # Parse info from caption
    caption = query.message.caption
    lines = caption.split("\n")
    try:
        name = lines[2].split(": ")[1].strip()
        anime = lines[3].split(": ")[1].strip()
    except:
        return await query.answer("❌ Error parsing metadata.")

    await query.answer("♻️ Re-hosting & Integrating...")
    await query.message.edit_reply_markup(None)

    status_msg = await query.message.reply_text("📥 Re-hosting to Catbox...")

    try:
        # Download from our own review group (Bot can do this)
        temp_path = await app.download_media(query.message.photo.file_id)
        final_url = await upload_image_to_catbox(temp_path)
        
        if not final_url:
            return await status_msg.edit_text("❌ Re-hosting failed.")

        rarity_text = RARITY_MAP[rarity_num]
        
        # Post to Channel
        channel_caption = (
            f"<b>Character Name:</b> {name}\n"
            f"<b>Anime Name:</b> {anime}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"<i>Approved by Admin</i>"
        )
        
        sent_msg = await app.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=final_url,
            caption=channel_caption,
            parse_mode=ParseMode.HTML
        )

        # DB Save
        char_data = {
            'img_url': final_url,
            'name': name,
            'anime': anime,
            'rarity': rarity_text,
            'message_id': sent_msg.id
        }
        
        char_id = await add_character_to_db(char_data)
        
        await status_msg.edit_text(f"✅ <b>Integrated!</b>\nName: {name}\nID: <code>{char_id}</code>")
        await query.message.delete()

    except Exception as e:
        LOGGER.error(f"Approval Error: {e}")
        await status_msg.edit_text(f"❌ Error: {e}")

@app.on_callback_query(filters.regex(r"^rsc_dec$"))
async def decline_scrape_callback(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Admin only.")
    await query.answer("❌ Declined.")
    await query.message.delete()
