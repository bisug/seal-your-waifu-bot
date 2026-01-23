import httpx
from pyrogram import filters, types, enums
from Grabber import app, LOGGER
from config import config

IMGBB_API_KEY = config.IMGBB_API_KEY

async def upload_to_imgbb(image_url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                data={'key': IMGBB_API_KEY, 'image': image_url},
                timeout=30
            )
            response_data = response.json()

            if response_data.get('success'):
                return response_data['data']['url']
        return None
    except Exception as e:
        LOGGER.error(f"Error uploading to ImgBB: {str(e)}")
        return None

@app.on_message(filters.command("tgm"))
async def tgm_cmd(_, message: types.Message) -> None:
    target_msg = message.reply_to_message if message.reply_to_message else message
    
    if not target_msg.photo:
        await message.reply_text("❌ Please send or reply to an image with this command.")
        return

    status_msg = await message.reply_text("⏳ Uploading to ImgBB...")
    
    try:
        # Pyrogram doesn't give direct file URL easily without a bot server or downloading.
        # However, we can download it to memory or use a direct link if it's already on TG servers.
        # Standard approach: Download and upload.
        
        file_path = await target_msg.download()
        
        with open(file_path, "rb") as f:
            image_data = f.read()
        
        # Uploading raw bytes is better than URL if we just downloaded it
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                data={'key': IMGBB_API_KEY, 'image': image_data},
                timeout=60
            )
            response_data = response.json()
            
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        if response_data.get('success'):
            imgbb_url = response_data['data']['url']
            await status_msg.delete()
            await message.reply_photo(photo=imgbb_url, caption=f"✅ **Image uploaded successfully!**\n🔗 `{imgbb_url}`")
        else:
            await status_msg.edit_text(f"❌ Failed to upload image: {response_data.get('error', {}).get('message', 'Unknown error')}")

    except Exception as e:
        LOGGER.error(f"Error in tgm_cmd: {e}")
        await status_msg.edit_text(f"❌ An error occurred during upload.")
