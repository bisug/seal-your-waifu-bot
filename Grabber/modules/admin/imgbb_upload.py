import os

import httpx
from pyrogram import enums, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import LOGGER, app
from Grabber.core.utils import reply_media_dynamic
from Grabber.core.waifu import upload_media_safely

IMGBB_API_KEY = config.IMGBB_API_KEY



@app.on_message(filters.command("tgm"))
async def tgm_cmd(_, message: types.Message) -> None:
    target_msg = message.reply_to_message if message.reply_to_message else message

    if not (target_msg.photo or getattr(target_msg, 'video', None) or getattr(target_msg, 'animation', None) or getattr(target_msg, 'document', None)):
        await message.reply_text("❌ <b>Please send or reply to an image or video with this command.</b>", parse_mode=ParseMode.HTML)
        return

    status_msg = await message.reply_text("⏳ <b>Uploading to ImgBB...</b>", parse_mode=ParseMode.HTML)

    try:




        file_path = await target_msg.download()

        remote_url = await upload_media_safely(file_path)

        if os.path.exists(file_path):
            os.remove(file_path)

        if remote_url:
            await status_msg.delete()
            await reply_media_dynamic(message, remote_url, caption=f"✅ <b>Media uploaded successfully!</b>\n🔗 <code>{remote_url}</code>", parse_mode=ParseMode.HTML)
        else:
            await status_msg.edit_text(f"❌ <b>Failed to securely host the media on Catbox or ImgBB.</b>", parse_mode=ParseMode.HTML)

    except Exception as e:
        LOGGER.error(f"Error in tgm_cmd: {e}")
        await status_msg.edit_text(f"❌ <b>An error occurred during upload.</b>", parse_mode=ParseMode.HTML)
