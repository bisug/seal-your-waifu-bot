import asyncio
import os
import re
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import (GALLERY_CHANNEL_ID, LOGGER, OWNER_ID, app, collection,
                    scraped_characters_collection, sudo_users, userbot, sudo_filter)
from Grabber.core.utils import handle_errors, send_media_dynamic
from Grabber.core.waifu import (add_character_to_db,
                                invalidate_character_cache,
                                upload_media_safely)
from Grabber.modules.collection.rarities import RARITY_MAP
# Hardcoded Review Group
LOG_GROUP_ID = config.LOG_GROUP_ID
# Global state to manage active scraping tasks
scraping_tasks = {}
pending_characters = set()
def clean_text(text: str) -> str:
    """Cleans text of brackets, counts, emojis, and extra whitespace."""
    if not text: return ""
    # 1. Remove bracket items like [🎒] or [x1]
    text = re.sub(r'\[.*?\]', '', text)
    # 2. Remove parenthetical counts like (x1) or (1/89)
    text = re.sub(r'\((?:x\s*)?\d+(?:/\d+)?\)', '', text, flags=re.I)
    # 3. Aggressively clean the end of the string to reveal IDs
    # Remove symbols, emojis, and whitespace from the very end
    text = re.sub(r'[^\w\s\.]+$', '', text)
    # 4. Remove trailing IDs (3+ digits) or counts like "x10"
    # We use \b to ensure we don't cut into a name like "Area 51" if it's not at the end
    text = re.sub(r'\s+x\d+\s*$', '', text, flags=re.I)
    text = re.sub(r'\s+\d{3,}\s*$', '', text)
    # 5. Handle cases where the ID might be stuck to the name "AnimeName12345" 
    # but only if clearly a long ID (5+ digits)
    text = re.sub(r'\d{5,}$', '', text)
    # 6. Global symbol cleaning
    text = text.replace('-', ' ').replace('_', ' ')
    text = re.sub(r'[^\w\s\.]+', '', text)
    # 7. Final normalization
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
def smart_parse_character(text: str):
    """
    Parses various character message formats using regex spanning 7+ formats.
    Returns (name, anime) or (None, None).
    """
    if not text: return None, None
    patterns = [
        # Format: 🌸 Hakari Hanazono \n ... 🏖️ From: The 100 Girlfriends ...
        (r'🌸\s*(?P<name>[^\n]+)\n.*?From:\s*(?P<anime>[^\n]+)', re.I | re.S),
        # Format: Name: Sabo ... Anime: One Piece
        (r'(?:\*Name\*|Name|NAME|Character):\s*(?P<name>[^\n]+)\n.*?(?:\*Anime\*|Anime|ANIME|Series|From|FROM):\s*(?P<anime>[^\n]+)', re.I | re.S),
        # Format: 1804: Mikasa Ackerman \n Attack On Titan \n ʀᴀʀɪᴛʏ:
        (r'(?:^|\n)\d+:\s*(?P<name>[^\n]+)\n(?P<anime>[^\n]+)\n.*?ʀᴀʀɪᴛʏ:', re.I | re.S),
        # Format: Anime\n 1234: Name
        (r'(?:^|\n)(?P<anime>[^\n]+)\n\d+:\s*(?P<name>[^\n]+)', re.I),
        # Format: Augusta [🎒] \n Anime: Wuthering Waves
        (r'(?:^|\n)(?P<name>[^\n]+?)\s*(?:\[.*?\])?\s*\n+(?:Anime|ANIME):\s*(?P<anime>[^\n]+)', re.I),
    ]
    for pattern, flags in patterns:
        match = re.search(pattern, text, flags=flags)
        if match:
            name = clean_text(match.group('name'))
            anime = clean_text(match.group('anime'))
            # Additional safety: ensure it's on a single line
            anime = anime.split('\n')[0].strip()
            if name and anime:
                return name, anime
    return None, None
def get_review_keyboard():
    """Buttons for selecting rarity or declining a character."""
    buttons = []
    # Rarity Choices (Dynamic based on RARITY_MAP)
    row = []
    for i in sorted(RARITY_MAP.keys()):
        rarity_full = RARITY_MAP[i]
        # Extract name part: "🟢 Medium" -> "Medium"
        rarity_name = rarity_full.split(" ", 1)[1] if " " in rarity_full else rarity_full
        row.append(types.InlineKeyboardButton(rarity_name, callback_data=f"rsc_app:{i}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([types.InlineKeyboardButton("❌ Decline", callback_data="rsc_dec")])
    return types.InlineKeyboardMarkup(buttons)
@app.on_message(filters.command("scrape") & sudo_filter)
@handle_errors
async def scrape_group_command_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage: `/scrape <group_id_or_username> [limit]`\n"
            "• `limit` — how many messages to scan (default: 5000)\n"
            "• Example: `/scrape @mygroup 400`\n"
            "Note: Bot/UserBot must be a member of the group."
        )
    if message.chat.id in scraping_tasks:
        return await message.reply_text("⚠️ A scraping task is already running. Use `/stop_scrape`.")
    target_chat = message.command[1]
    # Optional second argument: number of messages to scan
    scan_limit = 5000
    if len(message.command) >= 3:
        try:
            scan_limit = int(message.command[2])
            if scan_limit <= 0:
                return await message.reply_text("❌ Limit must be a positive number. Example: `/scrape @mygroup 400`")
        except ValueError:
            return await message.reply_text("❌ Invalid limit. Must be a number. Example: `/scrape @mygroup 400`")
    # Handle numeric IDs (including negative ones for groups/channels)
    try:
        if target_chat.startswith("-") or target_chat.isdigit():
            target_chat = int(target_chat)
    except ValueError:
        pass
    status = await app.send_message_safe(message.chat.id, f"⏳ Scanning `{target_chat}` for characters (limit: {scan_limit:,})...")
    try:
        # Use userbot for scraping. If missing or disconnected, report error.
        if config.STRING_SESSION:
            if not userbot:
                 return await app.edit_message_text_safe(status.chat.id, status.id, "❌ <b>UserBot is not initialized.</b>\nThis usually means the STRING_SESSION was invalid or missing during startup.")
            if not userbot.is_connected:
                return await app.edit_message_text_safe(status.chat.id, status.id, "❌ <b>UserBot is configured but not connected.</b>\nPlease check Heroku logs for auth errors or regenerate your session string.")
            client_to_use = userbot
        else:
            client_to_use = app # Fallback for public groups
        is_userbot = (client_to_use == userbot)
        # Resolve chat
        try:
            chat = await client_to_use.get_chat(target_chat)
        except (errors.PeerIdInvalid, errors.ChannelInvalid, errors.Forbidden) as e:
            error_tip = "Make sure Bot is added." if not is_userbot else "Make sure UserBot is a member."
            return await app.edit_message_text_safe(status.chat.id, status.id, f"❌ Could not access chat: {e}\n{error_tip}")
        except errors.RPCError as e:
            return await app.edit_message_text_safe(status.chat.id, status.id, f"❌ Access Error: {e}")


        scraping_tasks[message.chat.id] = True
        sent_count = 0
        try:
            # Iterate backwards through history up to the requested scan_limit
            async for msg in client_to_use.get_chat_history(chat.id, limit=scan_limit):
                if message.chat.id not in scraping_tasks:
                    break
                # Process only photos or docs (media)
                if not (msg.photo or msg.document):
                    continue
                caption = msg.caption or msg.text
                name, anime = smart_parse_character(caption)
                if not name or not anime:
                    continue
                key = (name.lower(), anime.lower())
                # pending_characters is a session-only in-memory fast-path cache.
                # scraped_characters_collection is the authoritative dedup store across restarts.
                if key in pending_characters:
                    continue
                # Check if exists locally
                exists = await collection.find_one({"name": name, "anime": anime})
                if exists:
                    continue
                # Check if already scraped/declined
                already_scraped = await scraped_characters_collection.find_one({"name": name, "anime": anime})
                if already_scraped:
                    continue
                temp_path = None
                try:
                    # Send for Review
                    # We download first to ensure we have a valid file to re-upload to our group
                    temp_path = await client_to_use.download_media(msg)
                    review_caption = (
                        f"<b>🆕 Scraped Character!</b>\n\n"
                        f"👤 <b>Name:</b> {name}\n"
                        f"🎬 <b>Anime:</b> {anime}\n\n"
                        "Select Rarity to Approve or Decline below:"
                    )
                    await send_media_dynamic(app, chat_id=LOG_GROUP_ID, media_url=temp_path,
                        caption=review_caption,
                        reply_markup=get_review_keyboard(),
                        parse_mode=enums.ParseMode.HTML
                    )
                    # Record as scraped to prevent re-sending
                    await scraped_characters_collection.insert_one({"name": name, "anime": anime})
                    pending_characters.add((name.lower(), anime.lower()))
                    sent_count += 1
                    await asyncio.sleep(1.5)
                    if sent_count >= 100:  # Increased batch limit
                        await app.send_message_safe(message.chat.id, f"✅ Batch of {sent_count} characters sent to review group. Run `/scrape` again for more.")
                        break
                except errors.FloodWait as e:
                    # Bug #7 fix: respect FloodWait inside the scraping loop
                    LOGGER.warning(f"FloodWait during scrape: sleeping {e.value}s")
                    await asyncio.sleep(e.value)
                    continue
                except errors.RPCError as e:
                    LOGGER.error(f"Scrape Error: {e}")
                    continue
                finally:
                    # Bug #1 fix: always clean up temp file, even on exception
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
            if sent_count == 0:
                await app.send_message_safe(message.chat.id, "✅ Scraping complete. No new characters found.")
            elif sent_count < 100:
                await app.send_message_safe(message.chat.id, f"✅ Scraping complete. Sent {sent_count} characters.")
        except errors.RPCError as e:
            LOGGER.error(f"Scraper Failed: {e}")
            if status:
                await app.edit_message_text_safe(status.chat.id, status.id, f"❌ Scraper Failed: {e}")
        finally:
            # Bug #2 fix: always clean up the task entry, regardless of how we exit
            scraping_tasks.pop(message.chat.id, None)
    except Exception as e:
        # Catch-all for the outer try block (covers setup errors before scraping begins)
        LOGGER.error(f"Scrape command failed unexpectedly: {e}", exc_info=True)
        if status:
            await app.edit_message_text_safe(status.chat.id, status.id, f"❌ Unexpected error: {e}")
@app.on_message(filters.command("stop_scrape") & sudo_filter)
@handle_errors
async def stop_scrape_handler(client, message):
    if message.chat.id in scraping_tasks:
        del scraping_tasks[message.chat.id]
        await app.send_message_safe(message.chat.id, "🛑 Scraper task stopped.")
    else:
        await app.send_message_safe(message.chat.id, "ℹ️ No active scraper task.")
@app.on_callback_query(filters.regex(r"^rsc_app:(\d+)$"))
async def approve_scrape_callback(client, query):
    if query.from_user.id not in sudo_users and query.from_user.id != OWNER_ID:
        return await query.answer("❌ Admin only.")
    rarity_num = int(query.data.split(":")[1])
    # Parse info from caption using regex — resilient to caption format changes
    # We strip HTML tags first to ensure the regex matches the clean text
    caption = query.message.caption or ""
    clean_caption = re.sub(r'<[^>]+>', '', caption)
    # Look for Name/Anime or Name/Series or Character/Anime pattern
    name_match = re.search(r"(?:Name|Character):\s*(.+)", clean_caption, re.I)
    anime_match = re.search(r"(?:Anime|Series):\s*(.+)", clean_caption, re.I)
    if not name_match or not anime_match:
        # Fallback to lines if regex fails
        lines = clean_caption.split("\n")
        name, anime = None, None
        for line in lines:
            if "Name:" in line or "Character:" in line:
                name = line.split(":", 1)[1].strip()
            if "Anime:" in line or "Series:" in line:
                anime = line.split(":", 1)[1].strip()
        if not name or not anime:
            return await query.answer("❌ Error parsing metadata.")
    else:
        name = name_match.group(1).strip()
        anime = anime_match.group(1).strip()
    # CRITICAL: Always run strings through clean_text one last time 
    # to remove any trailing IDs that might have been in the review message
    name = clean_text(name)
    anime = clean_text(anime)
    key = (name.lower(), anime.lower())
    if key in pending_characters:
        pending_characters.remove(key)
    await query.answer("♻️ Re-hosting & Integrating...")
    await app.edit_message_reply_markup_safe(query.message.chat.id, query.message.id, None)
    status_msg = await app.send_message_safe(query.message.chat.id, "📥 Re-hosting to Catbox...")
    try:
        # Bug #3 fix: use the message object directly — supports both photos and documents.
        # Accessing query.message.photo would crash if the scraped item was a document.
        temp_path = await app.download_media(query.message)
        final_url = await upload_media_safely(temp_path)
        if not final_url:
            return await app.edit_message_text_safe(status_msg.chat.id, status_msg.id, "❌ Re-hosting failed.")
        rarity_text = RARITY_MAP[rarity_num]
        invalidate_character_cache(rarity_text)
        # Post to Channel
        channel_caption = (
            f"<b>Character Name:</b> {name}\n"
            f"<b>Anime Name:</b> {anime}\n"
            f"<b>Rarity:</b> {rarity_text}\n"
            f"<i>Approved by Admin</i>"
        )
        sent_msg = await send_media_dynamic(app, chat_id=GALLERY_CHANNEL_ID, media_url=final_url,
            caption=channel_caption,
            parse_mode=enums.ParseMode.HTML
        )
        # DB Save
        char_data = {
            'img_url': final_url,
            'name': name,
            'anime': anime,
            'rarity': rarity_text,
            'message_id': sent_msg.id if sent_msg else None
        }
        char_id = await add_character_to_db(char_data)
        await app.edit_message_text_safe(status_msg.chat.id, status_msg.id, f"✅ <b>Integrated!</b>\nName: {name}\nID: <code>{char_id}</code>")
        await query.message.delete()


    except (errors.RPCError, RuntimeError) as e:
        LOGGER.error(f"Approval Error: {e}")
        await app.edit_message_text_safe(status_msg.chat.id, status_msg.id, f"❌ Error: {e}")
@app.on_callback_query(filters.regex(r"^rsc_dec$"))
async def decline_scrape_callback(client, query):
    if query.from_user.id not in sudo_users and query.from_user.id != OWNER_ID:
        return await query.answer("❌ Admin only.")
    # Attempt to remove from pending_characters if possible
    caption = query.message.caption or ""
    # Bug #5 fix: strip HTML tags before parsing, just like approve_scrape_callback does.
    # Without this, the regex captures HTML like "</b>" as part of the name/anime.
    caption = re.sub(r'<[^>]+>', '', caption)
    name_match = re.search(r"(?:Name|Character):\s*(.+)", caption, re.I)
    anime_match = re.search(r"(?:Anime|Series):\s*(.+)", caption, re.I)
    if name_match and anime_match:
        name = name_match.group(1).strip()
        anime = anime_match.group(1).strip()
        key = (name.lower(), anime.lower())
        # We don't remove from scraped_characters_collection here 
        # because the user explicitly wants them NOT to be re-sent.
        if key in pending_characters:
            pending_characters.remove(key)
    await query.answer("❌ Declined.")
    await query.message.delete()
