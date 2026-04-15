import asyncio
import os
import shlex
import urllib.parse

import httpx
from pyrogram import enums, errors, filters, types
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode

from Grabber import GALLERY_CHANNEL_ID, LOGGER, OWNER_ID, app, sudo_users
from Grabber.core.utils import html_escape, send_media_dynamic
from Grabber.core.waifu import (add_character_to_db,
                                invalidate_character_cache,
                                upload_media_safely)
from Grabber.database import collection
from Grabber.modules.collection.rarities import RARITY_MAP


def get_rarity_help():
    """Generates dynamic rarity map help text."""
    rarity_list = "\n".join([f"({v}={k})" for k, v in RARITY_MAP.items()])
    return (
        "<b>Format:</b>\n"
        "Reply to media: <code>/upload \"Name\" \"Anime\" RarityNum</code>\n"
        "With URL: <code>/upload URL \"Name\" \"Anime\" RarityNum</code>\n\n"
        "<b>Rarity Map:</b>\n"
        f"{rarity_list}"
    )

@app.on_message(filters.command("upload") & filters.user(sudo_users + [OWNER_ID]))
async def upload_waifu_handler(_, message: types.Message):
    # Use shlex to support quoted arguments (e.g. "Muzan Kibutsuji")
    cmd_text = message.text or message.caption
    if not cmd_text:
        return
        
    try:
        # Split command and keep quoted segments together
        args = shlex.split(cmd_text)[1:]
    except ValueError as e:
        return await message.reply_text(f"❌ <b>Parsing Error:</b> {e}")

    is_reply = bool(message.reply_to_message and (
        message.reply_to_message.photo or 
        message.reply_to_message.document or 
        getattr(message.reply_to_message, 'video', None) or 
        getattr(message.reply_to_message, 'animation', None)
    ))

    if is_reply:
        if len(args) < 3:
            return await message.reply_text(get_rarity_help(), parse_mode=ParseMode.HTML)
        name, anime, rarity_num = args[0], args[1], args[2]
        img_url = None
    elif len(args) >= 4:
        img_url, name, anime, rarity_num = args[0], args[1], args[2], args[3]
    else:
        return await message.reply_text(get_rarity_help(), parse_mode=ParseMode.HTML)

    try:
        rarity_num = int(rarity_num)
        if rarity_num not in RARITY_MAP:
            raise ValueError
    except ValueError:
        return await message.reply_text(f"❌ Rarity must be a valid number from the map.\n\n{get_rarity_help()}", parse_mode=ParseMode.HTML)

    char_name = name.strip().title()
    anime_name = anime.strip().title()
    rarity_text = RARITY_MAP[rarity_num]

    status = await message.reply_text("⏳ <b>Processing upload...</b>", parse_mode=ParseMode.HTML)
    temp_path = None

    try:
        # 1. Acquire Media
        if is_reply:
            await status.edit_text("📥 Downloading media from Telegram...")
            temp_path = await message.reply_to_message.download()
        else:
            parsed = urllib.parse.urlparse(img_url)
            if parsed.scheme not in ("http", "https"):
                return await status.edit_text("❌ Invalid media URL scheme. Only HTTP/HTTPS allowed.")

            await status.edit_text("📥 Fetching media from URL (10MB limit)...")
            
            # SECURE DOWNLOAD: Streaming with size limit
            MAX_SIZE = 10 * 1024 * 1024 # 10MB
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", img_url, timeout=20.0) as response:
                    if response.status_code != 200:
                        return await status.edit_text(f"❌ Failed to fetch media (HTTP {response.status_code}).")
                    
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > MAX_SIZE:
                        return await status.edit_text("❌ File is too large! (Max 10MB)")

                    ext = os.path.splitext(parsed.path)[1] or ".jpg"
                    temp_path = f"temp_{message.id}{ext}"
                    downloaded_size = 0
                    
                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            downloaded_size += len(chunk)
                            if downloaded_size > MAX_SIZE:
                                f.close()
                                os.remove(temp_path)
                                return await status.edit_text("❌ File reached 10MB limit and was terminated.")
                            f.write(chunk)

        if not temp_path or not os.path.exists(temp_path):
            return await status.edit_text("❌ Failed to retrieve media.")

        # 2. Upload Media
        await status.edit_text("☁️ Uploading Media to secure host...")
        final_url = await upload_media_safely(temp_path)

        if not final_url:
            return await status.edit_text("❌ Media upload failed (Catbox/ImgBB reject).")

        # 3. Finalize Database
        caption = (
            f"<b>Character Name:</b> {char_name}\n"
            f"<b>Anime Name:</b> {anime_name}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"Added by <a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>"
        )

        sent_msg = await send_media_dynamic(
            client=app,
            chat_id=GALLERY_CHANNEL_ID,
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
            f"✅ <b>Waifu Uploaded!</b>\nID: <code>{char_id}</code>\n"
            f"Name: {char_name}\n"
            f"Host: {'Catbox' if 'catbox' in final_url else 'ImgBB'}", 
            parse_mode=ParseMode.HTML
        )

    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        return await upload_waifu_handler(_, message)
    except Exception as e:
        LOGGER.error(f"Upload Failure: {e}")
        await status.edit_text(f"❌ Error: {html_escape(str(e))}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@app.on_message(filters.command(["delete", "del"]) & filters.user(sudo_users + [OWNER_ID]))
async def delete_waifu_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: <code>/delete &lt;id&gt;</code>", parse_mode=ParseMode.HTML)

    # Pad with leading zero if ID is short and purely numeric (matches DB format)
    raw_id = message.command[1]
    char_id = raw_id.zfill(2) if raw_id.isdigit() else raw_id

    # Find first to show confirmation
    character = await collection.find_one({'id': char_id})

    if not character:
        return await message.reply_text(f"❌ Character not found with ID: <code>{char_id}</code>", parse_mode=ParseMode.HTML)

    text = (
        f"⚠️ <b>Delete Confirmation</b>\n\n"
        f"Are you sure you want to delete this character?\n\n"
        f"🆔 ID: <code>{char_id}</code>\n"
        f"📛 Name: <b>{character['name']}</b>\n"
        f"🎬 Anime: {character['anime']}\n"
        f"🔮 Rarity: {character['rarity']}"
    )

    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"del_confirm:{char_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")
        ]
    ]

    await message.reply_text(
        text, 
        reply_markup=InlineKeyboardMarkup(buttons), 
        parse_mode=ParseMode.HTML
    )


@app.on_callback_query(filters.regex(r"^del_") & filters.user(sudo_users + [OWNER_ID]))
async def delete_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    action = data[0]

    if action == "del_cancel":
        await query.message.delete()
        return await query.answer("Deletion cancelled.")

    if action == "del_confirm":
        char_id = data[1]
        character = await collection.find_one_and_delete({'id': char_id})

        if character:
            msg_id = character.get('message_id')
            if msg_id:
                try:
                    await app.delete_messages(GALLERY_CHANNEL_ID, msg_id)
                except Exception as e:
                    LOGGER.debug(f"Failed to delete gallery message {msg_id}: {e}")
                    
            invalidate_character_cache(character.get('rarity'))
            await query.message.edit_text(
                f"✅ <b>Successfully Deleted!</b>\n"
                f"ID: <code>{char_id}</code>\n"
                f"Name: <b>{character['name']}</b>",
                parse_mode=ParseMode.HTML
            )
            await query.answer("Character deleted.")
        else:
            await query.answer("❌ Error: Character not found or already deleted.", show_alert=True)
            await query.message.delete()
