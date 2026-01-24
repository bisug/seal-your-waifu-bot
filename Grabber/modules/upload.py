from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import sudo_users, OWNER_ID, CHARA_CHANNEL_ID, LOGGER
from Grabber.core.waifu import upload_image_to_imgbb, add_character_to_db, get_character_by_id
from Grabber.database import collection

RARITY_MAP = {
    1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🪽 Shop", 9: "🫧 Royal", 10: "💎 Antique"
}

import asyncio
import os

@app.on_message(filters.command("upload") & filters.user(sudo_users + [OWNER_ID]))
async def upload_waifu_handler(_, message: types.Message):
    # Support both /upload <url> <name> <anime> <rarity> 
    # AND reply to image + /upload <name> <anime> <rarity>
    
    if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
        if len(message.command) < 4:
            return await message.reply_text("❌ <b>Usage (Reply):</b> <code>/upload &lt;name&gt; &lt;anime&gt; &lt;rarity_num&gt;</code>", parse_mode=enums.ParseMode.HTML)
        name, anime, rarity_num = message.command[1], message.command[2], message.command[3]
        is_reply = True
    elif len(message.command) == 5:
        img_url, name, anime, rarity_num = message.command[1], message.command[2], message.command[3], message.command[4]
        is_reply = False
    else:
        return await message.reply_text(
            "❌ <b>Invalid Format!</b>\n\n"
            "1️⃣ <b>Reply to Image:</b> <code>/upload &lt;name&gt; &lt;anime&gt; &lt;rarity_num&gt;</code>\n"
            "2️⃣ <b>Bulk URL:</b> <code>/upload &lt;url&gt; &lt;name&gt; &lt;anime&gt; &lt;rarity_num&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )

    try:
        rarity_num = int(rarity_num)
        if rarity_num not in RARITY_MAP:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Rarity must be between 1 and 10.")

    status = await message.reply_text("⏳ Processing upload...")
    temp_path = None

    try:
        if is_reply:
            await status.edit_text("📥 Downloading image...")
            temp_path = await message.reply_to_message.download()
        else:
            # For URL uploads, we'll download it first to support Catbox properly
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
            f"<b>Character Name:</b> {char_name}\n"
            f"<b>Anime Name:</b> {anime_name}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"Added by {message.from_user.mention}"
        )

        sent_msg = await app.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=final_url,
            caption=caption,
            parse_mode=enums.ParseMode.HTML
        )

        char_data = {
            'img_url': final_url,
            'name': char_name,
            'anime': anime_name,
            'rarity': rarity_text,
            'message_id': sent_msg.id
        }
        
        char_id = await add_character_to_db(char_data)
        await status.edit_text(f"✅ **Waifu Uploaded!**\nID: `{char_id}`\nHost: {'Catbox' if 'catbox' in final_url else 'ImgBB'}")

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
        return await message.reply_text("❌ Usage: <code>/delete &lt;id&gt;</code>", parse_mode=enums.ParseMode.HTML)

    char_id = message.command[1]
    character = await collection.find_one_and_delete({'id': char_id})

    if character:
        if character.get('message_id'):
            try:
                await app.delete_messages(CHARA_CHANNEL_ID, character['message_id'])
            except Exception:
                pass
        await message.reply_text(f"✅ Deleted ID: `{char_id}`")
    else:
        await message.reply_text("❌ Character not found.")
