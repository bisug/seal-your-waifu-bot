import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, collection, user_collection, OWNER_ID, CHARA_CHANNEL_ID, LOGGER
from Grabber.core.waifu import upload_image_to_catbox, add_character_to_db
from Grabber.core.utils import html_escape
from Grabber.modules.collection.rarities import RARITY_MAP
from config import config

# Configuration for Scraper Review
REVIEW_GROUP_ID = -1002767033399

# Dictionary to keep track of active scrapers
active_scrapers = {}

def clean_text(text: str) -> str:
    """Dynamically cleans name and anime name by removing common icons and extra spaces."""
    if not text:
        return ""
    # Remove icons like [🦋], [💮], etc.
    text = re.sub(r'\[.*?\]', '', text)
    # Remove emojis and other non-ascii (optional, but requested for cleanliness)
    # text = re.sub(r'[^\x00-\x7F]+', '', text) # Keeping it simple for now
    return text.strip()

def get_review_keyboard(char_id_in_remote: str):
    """Buttons for selecting rarity or declining a character."""
    buttons = []
    # Rarity Choices (Common to Legendary)
    row = []
    # We only show the common ones or all 10? User said "choosing rarity"
    # Let's show all 10 in small rows
    for i in range(1, 11):
        rarity_icon = RARITY_MAP[i].split(" ")[0]
        row.append(types.InlineKeyboardButton(rarity_icon, callback_data=f"sc_app:{i}:{char_id_in_remote}"))
        if len(row) == 5:
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

    mongo_uri = message.command[1]
    
    if active_scrapers.get(message.chat.id):
        return await message.reply_text("⚠️ Scraper is already running.")

    status = await message.reply_text("⏳ Connecting to remote database...")

    try:
        remote_client = AsyncIOMotorClient(mongo_uri)
        remote_db = remote_client['character_database']
        remote_col = remote_db['characters1']
        
        count = await remote_col.count_documents({})
        if count == 0:
            return await status.edit_text("❌ No characters found in that collection.")

        await status.edit_text(f"🔍 Found {count} characters. Starting continuous review process...\nUse `/stop_scrape` to stop.")
        
        active_scrapers[message.chat.id] = True
        
        # We store the cursor or just start iterating
        cursor = remote_col.find({})
        
        processed_count = 0
        async for char in cursor:
            # Check if we should stop
            if not active_scrapers.get(message.chat.id):
                break

            remote_id = str(char.get("_id"))
            name = clean_text(char.get("name", "Unknown"))
            anime = clean_text(char.get("anime", "Unknown"))
            image_id = char.get("image_id") 

            if not image_id:
                continue

            # Check duplication
            exists = await collection.find_one({"name": name, "anime": anime})
            if exists:
                continue

            try:
                # 1. Choose which client to use for sending to review
                from Grabber import userbot
                client_to_use = userbot if userbot else app

                caption = (
                    f"<b>👤 Name:</b> {name}\n"
                    f"<b>🎬 Anime:</b> {anime}\n\n"
                    "Select Rarity to Approve or Decline:"
                )
                
                await client_to_use.send_photo(
                    chat_id=REVIEW_GROUP_ID,
                    photo=image_id,
                    caption=caption,
                    reply_markup=get_review_keyboard(remote_id),
                    parse_mode=ParseMode.HTML
                )
                
                processed_count += 1
                # Small delay to avoid flood
                await asyncio.sleep(1)

            except Exception as e:
                LOGGER.error(f"Scraper Error for {name}: {e}")
                continue

        # Clean cleanup
        stopped_by_user = not active_scrapers.get(message.chat.id)
        active_scrapers.pop(message.chat.id, None)
        
        if stopped_by_user:
            await app.send_message(message.chat.id, f"🛑 Scraper stopped manually. Processed {processed_count} characters in this session.")
        else:
            await app.send_message(message.chat.id, f"✅ Scraper completed! Processed {processed_count} characters.")

    except Exception as e:
        LOGGER.error(f"Scraper Root Error: {e}")
        active_scrapers.pop(message.chat.id, None)
        await message.reply_text(f"❌ Scraper Failed: {e}")

@app.on_message(filters.command("stop_scrape") & filters.user(OWNER_ID))
async def stop_scrape_handler(client, message):
    if message.chat.id in active_scrapers:
        active_scrapers[message.chat.id] = False
        await message.reply_text("🛑 Stopping scraper... Please wait for current character to finish.")
    else:
        await message.reply_text("❌ No active scraper found.")

@app.on_callback_query(filters.regex(r"^sc_app:(\d+):(.+)$"))
async def approve_callback_handler(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Only the Owner can approve characters.", show_alert=True)

    data = query.data.split(":")
    rarity_num = int(data[1])
    remote_id = data[2]
    
    # Extract data from caption
    lines = query.message.caption.split("\n")
    name = lines[2].split(": ")[1].strip()
    anime = lines[3].split(": ")[1].strip()
    photo_id = query.message.photo.file_id # Use the one already sent to the group

    await query.answer("♻️ Migrating character...")
    await query.message.edit_reply_markup(None) # Remove buttons

    try:
        # 1. Download and Upload to Catbox (to have a permanent link)
        status_msg = await query.message.reply_text("📥 Downloading & Re-hosting...")
        
        # USE USERBOT IF AVAILABLE, ELSE FALLBACK TO MAIN APP
        from Grabber import userbot
        client_to_use = userbot if userbot else app
        
        temp_path = await client_to_use.download_media(photo_id)
        
        final_url = await upload_image_to_catbox(temp_path)
        if not final_url:
            return await status_msg.edit_text("❌ Image re-hosting failed.")

        rarity_text = RARITY_MAP[rarity_num]
        
        # 2. Post to Channel
        channel_caption = (
            f"<b>Character Name:</b> {name}\n"
            f"<b>Anime Name:</b> {anime}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"Approved by Admin"
        )
        
        channel_msg = await app.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=final_url,
            caption=channel_caption,
            parse_mode=ParseMode.HTML
        )

        # 3. Add to Main DB
        char_data = {
            'img_url': final_url,
            'name': name,
            'anime': anime,
            'rarity': rarity_text,
            'message_id': channel_msg.id
        }
        
        new_id = await add_character_to_db(char_data)
        
        await status_msg.edit_text(f"✅ <b>Successfully Integrated!</b>\nName: {name}\nID: <code>{new_id}</code>")
        await query.message.delete() # Remove the review request

    except Exception as e:
        LOGGER.error(f"Approval Error: {e}")
        await query.message.reply_text(f"❌ Integration Failed: {e}")

@app.on_callback_query(filters.regex(r"^sc_dec:(.+)$"))
async def decline_callback_handler(client, query):
    if query.from_user.id != OWNER_ID:
        return await query.answer("❌ Only Owner can decline.", show_alert=True)

    await query.answer("❌ Character Declined.")
    await query.message.delete()
