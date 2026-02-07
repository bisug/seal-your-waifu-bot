import asyncio
import os
import uuid
import httpx
from pyrogram import filters, enums, types
from Grabber import Grabberu, LOGGER

ENDPOINT = "https://api.trace.moe/search"
httpx_client = httpx.AsyncClient(timeout=60)

COMMANDS = ["reverse", "trace", "whatanime", "grs"]

class STRINGS:
    REPLY_TO_MEDIA = "ℹ️ Please reply to an anime screenshot (photo, sticker, or image file) to identify it."
    UNSUPPORTED_MEDIA_TYPE = "⚠️ **Unsupported media type!**\nℹ️ Please reply with a photo or document."
    REQUESTING_API_SERVER = "📡 Searching **Trace.moe** database... 📶"
    DOWNLOADING_MEDIA = "⏳ Downloading image..."
    UPLOADING_TO_API_SERVER = "📡 Identifying anime scene... 📶"
    PARSING_RESULT = "💻 Parsing match..."
    EXCEPTION_OCCURRED = "❌ **Error:** {}"
    RESULT = """
🌸 **Anime:** {title}
💎 **Similarity:** `{similarity}%`
🎞 **Episode:** `{episode}`
🎬 **At:** `{timestamp}`

🔗 [Anilist Link](https://anilist.co/anime/{anilist_id})
    """

@Grabberu.on_message(filters.command(COMMANDS))
async def on_trace_moe_search(_, message: types.Message):
    status_msg = None
    file_path = None
    
    try:
        if len(message.command) > 1:
            image_url = message.command[1]
            status_msg = await message.reply(STRINGS.REQUESTING_API_SERVER)
            response = await httpx_client.get(f"{ENDPOINT}?url={image_url}&anilistInfo")
        elif (reply := message.reply_to_message):
            if reply.media and reply.media in (enums.MessageMediaType.PHOTO, enums.MessageMediaType.STICKER, enums.MessageMediaType.DOCUMENT):
                status_msg = await message.reply(STRINGS.DOWNLOADING_MEDIA)
                
                if not os.path.exists("temp"):
                    os.makedirs("temp")
                    
                file_path = f"temp/{uuid.uuid4()}"
                await reply.download(file_path)
                
                await status_msg.edit(STRINGS.UPLOADING_TO_API_SERVER)
                with open(file_path, "rb") as image_file:
                    files = {"image": image_file}
                    response = await httpx_client.post(f"{ENDPOINT}?anilistInfo", files=files)
            else:
                return await message.reply(STRINGS.UNSUPPORTED_MEDIA_TYPE)
        else:
            return await message.reply(STRINGS.REPLY_TO_MEDIA)

        if response.status_code != 200:
            return await message.reply(STRINGS.EXCEPTION_OCCURRED.format(f"API Error ({response.status_code})"))

        data = response.json()
        if not data.get("result"):
            return await message.reply("❌ **No match found!** Try a clearer screenshot.", parse_mode=enums.ParseMode.MARKDOWN)

        # Get best match
        match = data["result"][0]
        anilist_id = match.get("anilist", {}).get("id") or match.get("anilist")
        title_info = match.get("anilist", {}).get("title", {})
        title = title_info.get("english") or title_info.get("romaji") or title_info.get("native") or "Unknown"
        
        similarity = round(match.get("similarity", 0) * 100, 2)
        episode = match.get("episode", "N/A")
        
        # Convert seconds to timestamp
        time_sec = match.get("from", 0)
        timestamp = f"{int(time_sec // 60):02d}:{int(time_sec % 60):02d}"

        text = STRINGS.RESULT.format(
            title=title,
            similarity=similarity,
            episode=episode,
            timestamp=timestamp,
            anilist_id=anilist_id
        )

        buttons = [[types.InlineKeyboardButton("🌐 View Source Video", url=match.get("video"))]] if match.get("video") else []

        await message.reply_photo(
            photo=match.get("image"),
            caption=text,
            reply_markup=types.InlineKeyboardMarkup(buttons) if buttons else None,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        
        if status_msg:
            await status_msg.delete()

    except Exception as e:
        LOGGER.error(f"Trace.moe search error: {e}", exc_info=True)
        error_text = STRINGS.EXCEPTION_OCCURRED.format(str(e))
        if status_msg:
            await status_msg.edit(error_text)
        else:
            await message.reply(error_text)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
