from pyrogram import Client, filters, enums, types
from pymongo import MongoClient
import re
from Grabber import LOGGER
from config import config

# MongoDB Connection from config
MONGO_URI = config.BATCH_MONGO_URI
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["CharacterDB"]
collection = db["Characters"]

# Credentials from config
STRING_SESSION =""
API_ID = config.API_ID
API_HASH =""
TOKEN =""

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
app = Client("batch_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

def extract_post_info(text: str):
    """Extracts channel username and post ID from a Telegram link."""
    match = re.match(r"https://t\.me/([^/]+)/(\d+)", text)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

@app.on_message(filters.command("batchids"))
async def batch_fetch(_, message: types.Message):
    """Fetches multiple posts and saves characters."""
    links = message.text.split()[1:]  # Get all provided links
    if not links:
        await message.reply("❌ Provide post links. Example:\n/batchid https://t.me/channel/1234 https://t.me/channel/5678")
        return

    processing_msg = await message.reply("⏳ Processing... Please wait!")
    saved_count = 0
    
    try:
        async with userbot:
            for link in links:
                channel, post_id = extract_post_info(link)
                if not channel:
                    await message.reply(f"⚠️ Invalid link: {link}")
                    continue
                
                try:
                    post = await userbot.get_messages(channel, post_id)
                    if not post.photo or not post.caption:
                        await message.reply(f"⚠️ No image or caption found in post: {link}")
                        continue
                    
                    # Extract character name from caption
                    character_name = None
                    formats = ["☘️ Name:", "🔸𝙽𝙰𝙼𝙴:", "🌟 Name:", "Character Name:", "◈𝗡𝗔𝗠𝗘:"]
                    for fmt in formats:
                        for line in post.caption.split("\n"):
                            if line.startswith(fmt):
                                character_name = line.replace(fmt, "").strip()
                                break
                        if character_name:
                            break
                    
                    if not character_name:
                        await message.reply(f"⚠️ Character name missing in post: {link}")
                        continue

                    file_id = post.photo.file_id
                    unique_id = post.photo.file_unique_id
                    
                    # Check for duplicates
                    if collection.find_one({"unique_id": unique_id}):
                        await message.reply(f"🔄 Already saved: {character_name}")
                        continue
                    
                    # Save to DB
                    collection.insert_one({
                        "file_id": file_id, 
                        "unique_id": unique_id, 
                        "name": character_name, 
                        "source": link
                    })
                    saved_count += 1

                except Exception as e:
                    await message.reply(f"❌ Error fetching post {link}: {e}")
                    LOGGER.error(f"Batch fetch error for {link}: {e}")

    except Exception as e:
        await message.reply(f"❌ Userbot failed to start: {e}")
        LOGGER.error(f"Userbot failed to start: {e}")

    await processing_msg.edit(f"✅ Batch Processing Completed!\n\nSaved Characters: {saved_count}")
