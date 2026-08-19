import inspect
from pymongo import AsyncMongoClient
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode
from urllib.parse import urlsplit, urlunsplit

from config import config
from backend import LOGGER, app
from backend.core.utils import handle_errors, html_escape

BACKUP_BATCH_SIZE = 500


def _redact_mongo_uri(uri: str) -> str:
    try:
        parts = urlsplit(uri)
        if not parts.scheme or not parts.netloc:
            return "<redacted>"
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        if "@" in parts.netloc:
            host = f"***:***@{host}"
        return urlunsplit((parts.scheme, host, parts.path, "", ""))
    except Exception:
        return "<redacted>"


async def _copy_collection(source_collection, dest_collection) -> int:
    copied = 0
    batch = []
    async for document in source_collection.find({}).batch_size(BACKUP_BATCH_SIZE):
        batch.append(document)
        if len(batch) >= BACKUP_BATCH_SIZE:
            await dest_collection.insert_many(batch, ordered=False)
            copied += len(batch)
            batch.clear()
    if batch:
        await dest_collection.insert_many(batch, ordered=False)
        copied += len(batch)
    return copied


async def _close_client(client) -> None:
    result = client.close()
    if inspect.isawaitable(result):
        await result

@app.on_message(filters.command("mongobackup") & filters.user(config.OWNER_ID))
@handle_errors
async def mongo_backup(_, message: types.Message) -> None:
    if len(message.command) != 4:
        await message.reply_text("❌ <b>Invalid command usage.</b>\nUse: <code>/mongobackup &lt;source_mongo&gt; &lt;destination_mongo&gt; &lt;db_name&gt;</code>", parse_mode=enums.ParseMode.HTML)
        return
    source_mongo, destination_mongo, db_name = message.command[1], message.command[2], message.command[3]
    source_client = None
    dest_client = None
    try:
        status_msg = await message.reply_text(
            (
                f"⏳ Starting backup of <code>{html_escape(db_name)}</code> from "
                f"<code>{html_escape(_redact_mongo_uri(source_mongo))}</code> to "
                f"<code>{html_escape(_redact_mongo_uri(destination_mongo))}</code>..."
            ),
            parse_mode=enums.ParseMode.HTML,
        )
        source_client = AsyncMongoClient(source_mongo)
        dest_client = AsyncMongoClient(destination_mongo)
        source_db = source_client[db_name]
        dest_db = dest_client[db_name]
        collections = await source_db.list_collection_names()
        total_documents = 0
        for collection_name in collections:
            source_collection = source_db[collection_name]
            dest_collection = dest_db[collection_name]
            total_documents += await _copy_collection(source_collection, dest_collection)
        await status_msg.edit_text(
            (
                f"✅ <b>Backup completed successfully for <code>{html_escape(db_name)}</code>!</b>\n"
                f"Copied <code>{total_documents:,}</code> documents across <code>{len(collections)}</code> collections."
            ),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        LOGGER.exception("Mongo backup failed")
        await message.reply_text(
            f"❌ <b>Backup failed!</b> Error: <code>{html_escape(str(e))}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    finally:
        if source_client:
            await _close_client(source_client)
        if dest_client:
            await _close_client(dest_client)
