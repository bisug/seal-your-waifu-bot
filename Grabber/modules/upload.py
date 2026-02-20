from pyrogram import enums, filters, types, errors
from pyrogram.enums import ParseMode
from Grabber import app
from Grabber import sudo_users, OWNER_ID, CHARA_CHANNEL_ID, LOGGER
from Grabber.core.waifu import upload_image_to_imgbb, add_character_to_db, get_character_by_id
from Grabber.database import collection
from Grabber.modules.rarities import RARITY_MAP

WRONG_FORMAT_TEXT = """Wrong ❌️ format...  eg. reply /upload muzan-kibutsuji Demon-slayer 3

img_url character-name anime-name rarity-number

use rarity number accordingly rarity Map

rarity_map = 
(⚪ Common=1)  
(🟠 Rare=2) 
(🟡 Legendary=3)
(🟢 Medium=4) 
(💠 Cosmic=5) 
(💮 Exclusive=6) 
(🔮 Limited Edition=7) 
(🪽 Shop=8) 
(🫧 royal=9) 
(💎 Antique=10)
"""

import asyncio
import os

@app.on_message(filters.command("upload") & filters.user(sudo_users + [OWNER_ID]))
async def upload_waifu_handler(_, message: types.Message):
                                                         
                                                          
    
    if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
        if len(message.command) < 4:
            return await message.reply_text(md_escape(WRONG_FORMAT_TEXT), parse_mode=ParseMode.MARKDOWN)
        name, anime, rarity_num = message.command[1], message.command[2], message.command[3]
        is_reply = True
    elif len(message.command) == 5:
        img_url, name, anime, rarity_num = message.command[1], message.command[2], message.command[3], message.command[4]
        is_reply = False
    else:
        return await message.reply_text(md_escape(WRONG_FORMAT_TEXT), parse_mode=ParseMode.MARKDOWN)

    try:
        rarity_num = int(rarity_num)
        if rarity_num not in RARITY_MAP:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Rarity must be between 1 and 10.", parse_mode=ParseMode.MARKDOWN)

    status = await message.reply_text("⏳ Processing upload...", parse_mode=ParseMode.MARKDOWN)
    temp_path = None

    try:
        if is_reply:
            await status.edit_text("📥 Downloading image...")
            temp_path = await message.reply_to_message.download()
        else:
                                                                                 
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(img_url)
                if resp.status_code == 200:
                    temp_path = f"temp_{message.id}.jpg"
                    with open(temp_path, "wb") as f:
                        f.write(resp.content)

        if not temp_path or not os.path.exists(temp_path):
            return await status.edit_text("❌ Failed to retrieve image.")

        await status.edit_text("☁️ Uploading to Catbox (Primary)...")
        from Grabber.core.waifu import upload_image_to_catbox, upload_image_to_imgbb
        
        final_url = await upload_image_to_catbox(temp_path)
        
        if not final_url:
            await status.edit_text("⚠️ Catbox failed. Using ImgBB backup...")
            final_url = await upload_image_to_imgbb(temp_path)

        if not final_url:
            return await status.edit_text("❌ Both Catbox and ImgBB failed to host the image.")

        char_name = name.replace('-', ' ').title()
        anime_name = anime.replace('-', ' ').title()
        rarity_text = RARITY_MAP[rarity_num]

        caption = (
            f"**Character Name:** {char_name}\n"
            f"**Anime Name:** {anime_name}\n"
            f"**Rarity:** {rarity_text}\n"
            f"Added by {message.from_user.mention}"
        )

        sent_msg = await app.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=final_url,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )

        char_data = {
            'img_url': final_url,
            'name': char_name,
            'anime': anime_name,
            'rarity': rarity_text,
            'message_id': sent_msg.id
        }
        
        char_id = await add_character_to_db(char_data)
        await status.edit_text(f"✅ **Waifu Uploaded!**\nID: `{char_id}`\nHost: {'Catbox' if 'catbox' in final_url else 'ImgBB'}", parse_mode=ParseMode.MARKDOWN)

    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await upload_waifu_handler(_, message)
    except Exception as e:
        LOGGER.error(f"Upload Failure: {e}")
        await status.edit_text(f"❌ Error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.on_message(filters.command(["delete", "delhete"]) & filters.user(sudo_users + [OWNER_ID]))
async def delete_waifu_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/delete <id>`", parse_mode=ParseMode.MARKDOWN)

    char_id = message.command[1]
    character = await collection.find_one_and_delete({'id': char_id})

    if character:
        if character.get('message_id'):
            try:
                await app.delete_messages(CHARA_CHANNEL_ID, character['message_id'])
            except Exception:
                pass
        await message.reply_text(f"✅ Deleted ID: `{char_id}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("❌ Character not found.", parse_mode=ParseMode.MARKDOWN)
