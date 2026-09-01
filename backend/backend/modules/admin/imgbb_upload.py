import os

from pyrogram import enums, filters, types

from backend.client import app
from backend.core.logging import get_logger
from backend.core.uploads import temp_download_dir
from backend.core.utils import handle_errors, reply_media_dynamic
from backend.core.waifu import upload_media_safely
from config import config

LOGGER = get_logger(__name__)
IMGBB_API_KEY = config.IMGBB_API_KEY
@app.on_message(filters.command("tgm"))
@handle_errors
async def tgm_cmd(_, message: types.Message) -> None:
    target_msg = message.reply_to_message if message.reply_to_message else message
    if not (target_msg.photo or getattr(target_msg, 'video', None) or getattr(target_msg, 'animation', None) or getattr(target_msg, 'document', None)):
        await message.reply_text("❌ <b>Please send or reply to an image or video with this command.</b>", parse_mode=enums.ParseMode.HTML)
        return
    status_msg = await message.reply_text("⏳ <b>Uploading to ImgBB...</b>", parse_mode=enums.ParseMode.HTML)
    try:
        # Absolute dir: kurigram 2.2.25 resolves relative paths against workdir.
        file_path = await target_msg.download(file_name=temp_download_dir("tgm") + "/")
        remote_url = await upload_media_safely(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            try:
                os.rmdir(os.path.dirname(file_path))
            except OSError:
                pass
        if remote_url:
            await status_msg.delete()
            await reply_media_dynamic(message, remote_url, caption=f"✅ <b>Media uploaded successfully!</b>\n🔗 <code>{remote_url}</code>", parse_mode=enums.ParseMode.HTML)
        else:
            await status_msg.edit_text("❌ <b>Failed to securely host the media on Catbox or ImgBB.</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error in tgm_cmd: {e}")
        await status_msg.edit_text("❌ <b>An error occurred during upload.</b>", parse_mode=enums.ParseMode.HTML)
