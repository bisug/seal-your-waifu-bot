import os
import asyncio
import urllib.parse
import httpx
from pyrogram import enums, filters, types, errors
from pyrogram.enums import ParseMode

from Grabber import app, sudo_users, OWNER_ID, CHARA_CHANNEL_ID, LOGGER
from Grabber.core.waifu import upload_media_safely, add_character_to_db, invalidate_character_cache
from Grabber.database import collection
from Grabber.modules.collection.rarities import RARITY_MAP
from Grabber.core.utils import send_media_dynamic, html_escape

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
(🎞️ AMV=11)
"""

@app.on_message(filters.command("upload") & filters.user(sudo_users + [OWNER_ID]))
async def upload_waifu_handler(_, message: types.Message):
    is_reply = bool(message.reply_to_message and (
        message.reply_to_message.photo or 
        message.reply_to_message.document or 
        getattr(message.reply_to_message, 'video', None) or 
        getattr(message.reply_to_message, 'animation', None)
    ))

    args = message.command[1:]

    if is_reply:
        if len(args) < 3:
            return await message.reply_text(WRONG_FORMAT_TEXT, parse_mode=ParseMode.HTML)
        name, anime, rarity_num = args[0], args[1], args[2]
        img_url = None
    elif len(args) == 4:
        img_url, name, anime, rarity_num = args[0], args[1], args[2], args[3]
    else:
        return await message.reply_text(WRONG_FORMAT_TEXT, parse_mode=ParseMode.HTML)

    try:
        rarity_num = int(rarity_num)
        if rarity_num not in RARITY_MAP:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Rarity must be between 1 and 11.", parse_mode=ParseMode.HTML)

    status = await message.reply_text("⏳ <b>Processing upload...</b>", parse_mode=ParseMode.HTML)
    temp_path = None

    try:
        # 1. Acquire Media
        if is_reply:
            await status.edit_text("📥 Downloading media...")
            temp_path = await message.reply_to_message.download()
        else:
            parsed = urllib.parse.urlparse(img_url)
            if parsed.scheme not in ("http", "https"):
                return await status.edit_text("❌ Invalid media URL scheme. Only HTTP/HTTPS allowed.", parse_mode=ParseMode.HTML)

            await status.edit_text("📥 Fetching media from URL...")
            async with httpx.AsyncClient() as client:
                resp = await client.get(img_url, timeout=30.0)
                if resp.status_code == 200:
                    ext = os.path.splitext(parsed.path)[1] or ".jpg"
                    temp_path = f"temp_{message.id}{ext}"
                    with open(temp_path, "wb") as f:
                        f.write(resp.content)
                else:
                    return await status.edit_text(f"❌ Failed to fetch media (HTTP {resp.status_code}).")

        if not temp_path or not os.path.exists(temp_path):
            return await status.edit_text("❌ Failed to retrieve media.")

        is_video = str(temp_path).endswith(('.mp4', '.webm', '.gif'))

        # 2. Upload Media
        await status.edit_text("☁️ Uploading Media (Catbox/ImgBB)...")
        final_url = await upload_media_safely(temp_path)

        if not final_url:
            return await status.edit_text("❌ Failed to securely host the media on Catbox or ImgBB.")

        # 3. Finalize Database
        char_name = name.replace('-', ' ').title()
        anime_name = anime.replace('-', ' ').title()
        rarity_text = RARITY_MAP[rarity_num]

        caption = (
            f"<b>Character Name:</b> {char_name}\n"
            f"<b>Anime Name:</b> {anime_name}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"Added by <a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>"
        )

        sent_msg = await send_media_dynamic(
            client=app,
            chat_id=CHARA_CHANNEL_ID,
            media_url=final_url,
            caption=caption,
            parse_mode=ParseMode.HTML
        )

        char_data = {
            'img_url': final_url,
            'name': char_name,
            'anime': anime_name,
            'rarity': rarity_text,
            'message_id': sent_msg.id
        }

        char_id = await add_character_to_db(char_data)
        invalidate_character_cache(rarity_text)
        
        await status.edit_text(
            f"✅ <b>Waifu Uploaded!</b>\nID: <code>{char_id}</code>\nHost: {'Catbox' if 'catbox' in final_url else 'ImgBB'}", 
            parse_mode=ParseMode.HTML
        )

    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await upload_waifu_handler(_, message) # '_' represents client here
    except Exception as e:
        LOGGER.error(f"Upload Failure: {e}")
        await status.edit_text(f"❌ Error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                LOGGER.warning(f"Failed to cleanup {temp_path}: {cleanup_err}")

@app.on_message(filters.command(["delete", "delhete"]) & filters.user(sudo_users + [OWNER_ID]))
async def delete_waifu_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: <code>/delete &lt;id&gt;</code>", parse_mode=ParseMode.HTML)

    char_id = message.command[1]
    character = await collection.find_one_and_delete({'id': char_id})

    if character:
        msg_id = character.get('message_id')
        if msg_id:
            try:
                await app.delete_messages(CHARA_CHANNEL_ID, msg_id)
            except Exception as e:
                LOGGER.warning(f"Failed to delete channel message {msg_id}: {e}")
                
        invalidate_character_cache(character.get('rarity'))
        await message.reply_text(f"✅ Deleted ID: <code>{char_id}</code>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("❌ Character not found.", parse_mode=ParseMode.HTML)
