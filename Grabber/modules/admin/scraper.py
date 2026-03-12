import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, collection, user_collection, OWNER_ID, CHARA_CHANNEL_ID, LOGGER, userbot
from Grabber.core.waifu import upload_image_to_catbox, add_character_to_db
from Grabber.core.utils import html_escape
from Grabber.modules.collection.rarities import RARITY_MAP
from config import config

# Configuration for Scraper Review
# The user wants this hardcoded or from config. We already have it in scraper.py as hardcoded.
REVIEW_GROUP_ID = -1002767033399

# Global state to manage active scraping tasks
scraping_tasks = {}

def clean_text(text: str) -> str:
    """Dynamically cleans name and anime name by removing common icons and extra spaces."""
    if not text:
        return ""
    # Remove emojis and special bracketed icons like [🦋]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove common emojis/special characters (simplified)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()

def get_review_keyboard(char_id_in_remote: str):
    """Buttons for selecting rarity or declining a character."""
    buttons = []
    # Rarity Choices (1-10)
    row = []
    for i in range(1, 11):
        rarity_full = RARITY_MAP.get(i, "Unknown")
        # Extract just the name (e.g., "Common" from "⚪ Common")
        rarity_name = rarity_full.split(" ")[1] if " " in rarity_full else rarity_full
        
        row.append(types.InlineKeyboardButton(rarity_name, callback_data=f"sc_app:{i}:{char_id_in_remote}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    # Decline Action
    buttons.append([types.InlineKeyboardButton("❌ Decline", callback_data=f"sc_dec:{char_id_in_remote}")])
    return types.InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("scrape") & filters.user(OWNER_ID))
async def scrape_command_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/scrape <mongo_uri>`")

    if message.chat.id in scraping_tasks:
        return await message.reply_text("⚠️ A scraping task is already running. Use `/stop_scrape` to kill it first.")

    mongo_uri = message.command[1]
    status = await message.reply_text("⏳ Connecting to remote database...")

    try:
        remote_client = AsyncIOMotorClient(mongo_uri)
        # Based on user request: database 'character_database', collection 'characters1'
        remote_db = remote_client['character_database']
        remote_col = remote_db['characters1']
        
        count = await remote_col.count_documents({})
        if count == 0:
            return await status.edit_text("❌ No characters found in remote collection 'characters1'.")

        await status.edit_text(f"🔍 Connected! Found {count} records.\nStarting review batch in the review group...\n(Use `/stop_scrape` to cancel)")
        
        scraping_tasks[message.chat.id] = True
        sent_count = 0
        
        cursor = remote_col.find({})
        async for char in cursor:
            # Check for stop signal
            if message.chat.id not in scraping_tasks:
                break

            remote_id = str(char.get("_id"))
            name = clean_text(char.get("name", "Unknown"))
            anime = clean_text(char.get("anime", "Unknown"))
            image_id = char.get("image_id")

            if not image_id:
                continue

            # Skip if already exists locally
            exists = await collection.find_one({"name": name, "anime": anime})
            if exists:
                continue

            try:
                caption = (
                    f"<b>🆕 Scraped Character!</b>\n\n"
                    f"👤 <b>Name:</b> {name}\n"
                    f"🎬 <b>Anime:</b> {anime}\n\n"
                    "Select Rarity to Approve or Decline below:"
                )
                
                # CRITICAL: If image_id is from another bot, MainBot will fail ("Failed to decode").
                # We use the Userbot if available to send the preview.
                sender = userbot if userbot else app
                
                await sender.send_photo(
                    chat_id=REVIEW_GROUP_ID,
                    photo=image_id,
                    caption=caption,
                    reply_markup=get_review_keyboard(remote_id),
                    parse_mode=ParseMode.HTML
                )
                
                sent_count += 1
                await asyncio.sleep(2) # Avoid spamming the group too fast

                # Limit batch to 10 characters per run to prevent runaway loops
                if sent_count >= 10:
                    await message.reply_text("✅ Batch of 10 characters sent for review. Run `/scrape` again for more.")
                    break

            except Exception as e:
                LOGGER.error(f"Scraper Preview Error for {name}: {e}")
                # If even userbot fails to decode, this file_id might be invalid or restricted
                continue

        if message.chat.id in scraping_tasks:
            del scraping_tasks[message.chat.id]
            if sent_count == 0:
                await message.reply_text("✅ Scraping complete. No new characters found.")
            elif sent_count < 10:
                await message.reply_text(f"✅ Scraping session complete. Sent {sent_count} characters.")

    except Exception as e:
        LOGGER.error(f"Scraper Root Error: {e}")
        if message.chat.id in scraping_tasks:
            del scraping_tasks[message.chat.id]
        await status.edit_text(f"❌ Scraper Failed: {e}")

@app.on_message(filters.command("stop_scrape") & filters.user(OWNER_ID))
async def stop_scrape_handler(client, message):
    if message.chat.id in scraping_tasks:
        del scraping_tasks[message.chat.id]
        await message.reply_text("🛑 Scraper task has been stopped.")
    else:
        await message.reply_text("ℹ️ No active scraper task found.")

@app.on_callback_query(filters.regex(r"^sc_app:(\d+):(.+)$"))
async def approve_callback_handler(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Only the Owner can approve characters.", show_alert=True)

    data = query.data.split(":")
    rarity_num = int(data[1])
    # remote_id = data[2] # Unused if we have caption

    # Parse metadata from caption
    caption_lines = query.message.caption.split("\n")
    try:
        name = caption_lines[2].split(": ")[1].strip()
        anime = caption_lines[3].split(": ")[1].strip()
    except Exception:
        return await query.answer("❌ Error parsing character info from caption.", show_alert=True)

    # Use the photo that was successfully sent to the group
    photo_id = query.message.photo.file_id

    await query.answer("♻️ Processing approval...")
    await query.message.edit_reply_markup(None) # Remove buttons to prevent double-click

    status_msg = await query.message.reply_text("📥 Re-hosting image to Catbox...")

    try:
        # Download using Userbot if available (more likely to have access to old File IDs)
        client_to_use = userbot if userbot else app
        temp_path = await client_to_use.download_media(photo_id)
        
        if not temp_path:
             return await status_msg.edit_text("❌ Failed to download image from Telegram.")

        final_url = await upload_image_to_catbox(temp_path)
        if not final_url:
            return await status_msg.edit_text("❌ Image re-hosting failed (Catbox).")

        rarity_text = RARITY_MAP.get(rarity_num, "Common")
        
        # 1. Post to Announcement Channel
        channel_caption = (
            f"<b>Character Name:</b> {name}\n"
            f"<b>Anime Name:</b> {anime}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"<i>Approved & Integrated by Admin</i>"
        )
        
        channel_msg = await app.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=final_url,
            caption=channel_caption,
            parse_mode=ParseMode.HTML
        )

        # 2. Insert into Main Character Collection
        char_data = {
            'img_url': final_url,
            'name': name,
            'anime': anime,
            'rarity': rarity_text,
            'message_id': channel_msg.id if channel_msg else None
        }
        
        char_id = await add_character_to_db(char_data)
        
        await status_msg.edit_text(f"✅ <b>Integrated!</b>\nName: {name}\nID: <code>{char_id}</code>")
        # Cleanup the review message
        await query.message.delete()

    except Exception as e:
        LOGGER.error(f"Approval Integration Error: {e}")
        await status_msg.edit_text(f"❌ Integration Failed: {e}")

@app.on_callback_query(filters.regex(r"^sc_dec:(.+)$"))
async def decline_callback_handler(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Only the Owner can decline characters.", show_alert=True)

    await query.answer("❌ Character Declined.")
    await query.message.delete()
