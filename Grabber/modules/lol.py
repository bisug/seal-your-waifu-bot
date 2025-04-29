import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# Logging Configuration
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Allowed user ID (only this user can run the command)
ALLOWED_USER_ID = 7717913705  # Replace with the actual Telegram User ID

async def mongo_backup(update: Update, context: CallbackContext) -> None:
    """Backup MongoDB data from one instance to another."""
    user_id = update.effective_user.id
    
    # Check if the user is authorized
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("❌ Permission Denied: You are not authorized to use this command.")
        return

    # Ensure correct number of arguments
    if len(context.args) != 3:
        await update.message.reply_text("❌ Invalid command usage.\nUse: `/mongobackup <source_mongo> <destination_mongo> <db_name>`", parse_mode="Markdown")
        return

    source_mongo, destination_mongo, db_name = context.args

    try:
        await update.message.reply_text(f"⏳ Starting backup of `{db_name}` from `{source_mongo}` to `{destination_mongo}`...", parse_mode="Markdown")

        # Connect to source and destination MongoDB
        source_client = AsyncIOMotorClient(source_mongo)
        dest_client = AsyncIOMotorClient(destination_mongo)

        source_db = source_client[db_name]
        dest_db = dest_client[db_name]

        # Fetch collection names
        collections = await source_db.list_collection_names()

        for collection_name in collections:
            source_collection = source_db[collection_name]
            dest_collection = dest_db[collection_name]

            # Fetch all documents
            documents = await source_collection.find({}).to_list(length=None)
            if documents:
                await dest_collection.insert_many(documents)

        await update.message.reply_text(f"✅ Backup completed successfully for `{db_name}`!", parse_mode="Markdown")

    except Exception as e:
        LOGGER.error(f"Backup Error: {e}")
        await update.message.reply_text(f"❌ Backup failed! Error: `{e}`", parse_mode="Markdown")

# Register the command handler
mongo_backup_handler = CommandHandler("mongobackup", mongo_backup, block=False)
