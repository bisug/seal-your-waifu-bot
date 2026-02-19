from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import filters, types, enums
from Grabber import app, LOGGER

                                                      
ALLOWED_USER_ID = 6574393060                                            

@app.on_message(filters.command("mongobackup") & filters.user(ALLOWED_USER_ID))
async def mongo_backup(_, message: types.Message) -> None:
                                                           
                                        
    if len(message.command) != 4:
        await message.reply_text("❌ Invalid command usage.\nUse: `/mongobackup <source_mongo> <destination_mongo> <db_name>`", parse_mode=enums.ParseMode.MARKDOWN)
        return

    source_mongo, destination_mongo, db_name = message.command[1], message.command[2], message.command[3]

    try:
        status_msg = await message.reply_text(f"⏳ Starting backup of `{db_name}` from `{source_mongo}` to `{destination_mongo}`...", parse_mode=enums.ParseMode.MARKDOWN)

                                                   
        source_client = AsyncIOMotorClient(source_mongo)
        dest_client = AsyncIOMotorClient(destination_mongo)

        source_db = source_client[db_name]
        dest_db = dest_client[db_name]

                                
        collections = await source_db.list_collection_names()

        for collection_name in collections:
            source_collection = source_db[collection_name]
            dest_collection = dest_db[collection_name]

                                 
            documents = await source_collection.find({}).to_list(length=None)
            if documents:
                await dest_collection.insert_many(documents)

        await status_msg.edit_text(f"✅ Backup completed successfully for `{db_name}`!", parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        LOGGER.error(f"Backup Error: {e}")
        await message.reply_text(f"❌ Backup failed! Error: `{e}`", parse_mode=enums.ParseMode.MARKDOWN)
