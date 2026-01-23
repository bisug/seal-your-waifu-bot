from pyrogram import filters, types, enums, errors
from Grabber.app import app
from Grabber import sudo_users, OWNER_ID, CHARA_CHANNEL_ID, LOGGER
from Grabber.core.waifu import upload_image_to_imgbb, add_character_to_db, get_character_by_id
from Grabber.database import collection

RARITY_MAP = {
    1: "⚪ Common", 2: "🟠 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💠 Cosmic",
    6: "💮 Exclusive", 7: "🔮 Limited Edition", 8: "🪽 Shop", 9: "🫧 Royal", 10: "💎 Antique"
}

@app.on_message(filters.command("upload") & filters.user(sudo_users + [OWNER_ID]))
async def upload_waifu_handler(_, message: types.Message):
    if len(message.command) != 5:
        return await message.reply_text("❌ **Format:** `/upload <url> <name> <anime> <rarity_num>`")

    img_url, name, anime, rarity_num = message.command[1], message.command[2], message.command[3], message.command[4]
    
    try:
        rarity_num = int(rarity_num)
        if rarity_num not in RARITY_MAP:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Rarity must be between 1 and 10.")

    status = await message.reply_text("⏳ Processing upload...")
    await app.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)

    try:
        # Business logic: Upload to ImgBB
        final_url = await upload_image_to_imgbb(img_url)
        if not final_url:
            return await status.edit_text("❌ Failed to process image URL.")

        char_name = name.replace('-', ' ').title()
        anime_name = anime.replace('-', ' ').title()
        rarity_text = RARITY_MAP[rarity_num]

        # Business logic: Database and Channel
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
        await status.edit_text(f"✅ **Waifu Uploaded!**\nID: `{char_id}`")

    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await upload_waifu_handler(_, message)
    except Exception as e:
        LOGGER.error(f"Upload Failure: {e}")
        await status.edit_text(f"❌ Error: {e}")

@app.on_message(filters.command(["delete", "delhete"]) & filters.user(sudo_users + [OWNER_ID]))
async def delete_waifu_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/delete <id>`")

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
