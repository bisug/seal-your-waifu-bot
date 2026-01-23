import asyncio
import os
import uuid
import httpx
from pyrogram import filters, enums, types
from Grabber import Grabberu, LOGGER
from config import config

ENDPOINT = config.GOOGLE_SEARCH_ENDPOINT
httpx_client = httpx.AsyncClient(timeout=60)

COMMANDS = ["reverse", "grs", "gis", "pp"]

class STRINGS:
    REPLY_TO_MEDIA = "ℹ️ Please reply to a message that contains one of the supported media types, such as a photo, sticker, or image file."
    UNSUPPORTED_MEDIA_TYPE = "⚠️ <b>Unsupported media type!</b>\nℹ️ Please reply with a supported media type: image, sticker, or image file."
    REQUESTING_API_SERVER = "📡 Requesting to <b>API Server</b>... 📶"
    DOWNLOADING_MEDIA = "⏳ Downloading media..."
    UPLOADING_TO_API_SERVER = "📡 Uploading media to <b>API Server</b>... 📶"
    PARSING_RESULT = "💻 Parsing result..."
    EXCEPTION_OCCURRED = "❌ <b>Exception occurred!</b>\n\n<b>Exception:</b> {}"
    RESULT = """
🔤 <b>Query:</b> {query}
🔗 <b>Page Link:</b> <a href="{search_url}">Link</a>

⌛️ <b>Time Taken:</b> <code>{time_taken}</code> ms.
🧑‍💻 <b>Credits:</b> @sukuna201
    """
    OPEN_SEARCH_PAGE = "↗️ Open Search Page"

@Grabberu.on_message(filters.command(COMMANDS))
async def on_google_lens_search(_, message: types.Message):
    response = None
    start_time = 0
    status_msg = None
    
    try:
        if len(message.command) > 1:
            image_url = message.command[1]
            params = {"image_url": image_url}
            status_msg = await message.reply(STRINGS.REQUESTING_API_SERVER)
            start_time = asyncio.get_event_loop().time()
            response = await httpx_client.get(ENDPOINT, params=params)
        elif (reply := message.reply_to_message):
            if reply.media and reply.media in (enums.MessageMediaType.PHOTO, enums.MessageMediaType.STICKER, enums.MessageMediaType.DOCUMENT):
                status_msg = await message.reply(STRINGS.DOWNLOADING_MEDIA)
                
                # Ensure temp directory exists
                if not os.path.exists("temp"):
                    os.makedirs("temp")
                    
                file_path = f"temp/{uuid.uuid4()}"
                try:
                    await reply.download(file_path)
                except Exception as exc:
                    await message.reply(STRINGS.EXCEPTION_OCCURRED.format(exc))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return
                
                with open(file_path, "rb") as image_file:
                    start_time = asyncio.get_event_loop().time()
                    files = {"file": image_file}
                    await status_msg.edit(STRINGS.UPLOADING_TO_API_SERVER)
                    response = await httpx_client.post(ENDPOINT, files=files)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                await message.reply(STRINGS.UNSUPPORTED_MEDIA_TYPE)
                return
        else:
            await message.reply(STRINGS.REPLY_TO_MEDIA)
            return

        if not response:
            await message.reply("❌ Internal error: No response from API.")
            return

        if response.status_code == 404:
            text = STRINGS.EXCEPTION_OCCURRED.format(response.json().get("error", "Not Found"))
            await message.reply(text)
            if status_msg: await status_msg.delete()
            return
        elif response.status_code != 200:
            text = STRINGS.EXCEPTION_OCCURRED.format(response.text)
            await message.reply(text)
            if status_msg: await status_msg.delete()
            return

        await status_msg.edit(STRINGS.PARSING_RESULT)
        response_json = response.json()
        query = response_json.get("query", "")
        search_url = response_json.get("search_url", "")
        end_time = asyncio.get_event_loop().time() - start_time
        time_taken = "{:.2f}".format(end_time)
        
        text = STRINGS.RESULT.format(
            query=f"<code>{query}</code>" if query else "<i>Name not found</i>",
            search_url=search_url,
            time_taken=time_taken
        )
        buttons = [[types.InlineKeyboardButton(STRINGS.OPEN_SEARCH_PAGE, url=search_url)]]
        await message.reply(
            text, 
            disable_web_page_preview=True, 
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        await status_msg.delete()

    except Exception as e:
        LOGGER.error(f"Error in Google Lens search: {e}", exc_info=True)
        if status_msg:
            await status_msg.edit(STRINGS.EXCEPTION_OCCURRED.format(str(e)))
        else:
            await message.reply(STRINGS.EXCEPTION_OCCURRED.format(str(e)))
