from pyrogram import Client, filters, enums, types
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from motor.motor_asyncio import AsyncIOMotorClient
import re
from Grabber import LOGGER
from config import config

                                
MONGO_URI = config.BATCH_MONGO_URI
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["CharacterDB"]
collection = db["Characters"]

                         
STRING_SESSION =""
API_ID = config.API_ID
API_HASH =""
TOKEN =""

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
app = Client("batch_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

def extract_post_info(text: str):
                                                                     
    match = re.match(r"https://t\.me/([^/]+)/(\d+)", text)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

@app.on_message(filters.command("batchids"))
async def batch_fetch(_, message: types.Message):
                                                      
    links = message.text.split()[1:]                          
    if not links:
        await message.reply("❌ <b>Provide post links.</b> Example:\n<code>/batchid https://t.me/channel/1234 https://t.me/channel/5678</code>", parse_mode=ParseMode.HTML)
        return

    processing_msg = await message.reply("⏳ <b>Processing... Please wait!</b>", parse_mode=ParseMode.HTML)
    saved_count = 0
    
    try:
        async with userbot:
            for link in links:
                channel, post_id = extract_post_info(link)
                if not channel:
                    await message.reply(f"⚠️ Invalid link: <code>{html_escape(link)}</code>", parse_mode=ParseMode.HTML)
                    continue
                
                try:
                    post = await userbot.get_messages(channel, post_id)
                    if not post.photo or not post.caption:
                        await message.reply(f"⚠️ No image or caption found in post: <code>{html_escape(link)}</code>", parse_mode=ParseMode.HTML)
                        continue
                    
                                                         
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
                        await message.reply(f"⚠️ Character name missing in post: <code>{html_escape(link)}</code>", parse_mode=ParseMode.HTML)
                        continue

                    file_id = post.photo.file_id
                    unique_id = post.photo.file_unique_id
                    
                                          
                    if await collection.find_one({"unique_id": unique_id}):
                        await message.reply(f"🔄 Already saved: <b>{html_escape(character_name)}</b>", parse_mode=ParseMode.HTML)
                        continue
                    
                                
                    await collection.insert_one({
                        "file_id": file_id, 
                        "unique_id": unique_id, 
                        "name": character_name, 
                        "source": link
                    })
                    saved_count += 1

                except Exception as e:
                    await message.reply(f"❌ Error fetching post <code>{html_escape(link)}</code>: <code>{html_escape(str(e))}</code>", parse_mode=ParseMode.HTML)
                    LOGGER.error(f"Batch fetch error for {link}: {e}")

    except Exception as e:
        await message.reply(f"❌ Userbot failed to start: <code>{html_escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        LOGGER.error(f"Userbot failed to start: {e}")

    await processing_msg.edit(f"✅ <b>Batch Processing Completed!</b>\n\nSaved Characters: <code>{saved_count}</code>", parse_mode=ParseMode.HTML)
