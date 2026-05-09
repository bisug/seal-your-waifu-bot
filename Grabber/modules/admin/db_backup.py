from pymongo import AsyncMongoClient
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import LOGGER, app
from Grabber.core.utils import handle_errors

@app.on_message(filters.command("mongobackup") & filters.user(config.OWNER_ID))
@handle_errors
async def mongo_backup(_, message: types.Message) -> None:
    if len(message.command) != 4:
        await message.reply_text("❌ <b>Invalid command usage.</b>\nUse: <code>/mongobackup &lt;source_mongo&gt; &lt;destination_mongo&gt; &lt;db_name&gt;</code>", parse_mode=enums.ParseMode.HTML)
        return
    source_mongo, destination_mongo, db_name = message.command[1], message.command[2], message.command[3]
    try:
        status_msg = await message.reply_text(f"⏳ Starting backup of <code>{db_name}</code> from <code>{source_mongo}</code> to <code>{destination_mongo}</code>...", parse_mode=enums.ParseMode.HTML)
        source_client = AsyncMongoClient(source_mongo)
        dest_client = AsyncMongoClient(destination_mongo)
        source_db = source_client[db_name]
        dest_db = dest_client[db_name]
        collections = await source_db.list_collection_names()
        for collection_name in collections:
            source_collection = source_db[collection_name]
            dest_collection = dest_db[collection_name]
            documents = await source_collection.find({}).to_list(length=None)
            if documents:
                await dest_collection.insert_many(documents)
        await status_msg.edit_text(f"✅ <b>Backup completed successfully for <code>{db_name}</code>!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Backup Error: {e}")
        await message.reply_text(f"❌ <b>Backup failed!</b> Error: <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
