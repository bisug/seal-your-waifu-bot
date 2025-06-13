from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from pymongo.errors import PyMongoError
import asyncio

from Grabber import (
    application, PHOTO_URL, OWNER_ID,
    user_collection, top_global_groups_collection,
    group_user_totals_collection, sudo_users as SUDO_USERS
)

OWNER_ID = 7717913705

# Broadcast Command
async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only for Sudo users...")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message text>")
        return

    message_text = " ".join(context.args)
    sent_count = 0
    failed_count = 0

    try:
        cursor = user_collection.find({})
        async for user in cursor:
            user_id = user.get("id")
            if not user_id:
                continue
            try:
                await context.bot.send_message(chat_id=user_id, text=message_text)
                sent_count += 1
                await asyncio.sleep(0.1)
            except Exception:
                failed_count += 1

        await update.message.reply_text(
            f"📢 Broadcast Summary:\n\n"
            f"👥 Total users: {sent_count + failed_count}\n"
            f"✅ Successfully sent: {sent_count}\n"
            f"❌ Failed to send: {failed_count}"
        )

    except PyMongoError as e:
        await update.message.reply_text(f"Database error: {str(e)}")
        
# Eval Command
async def eval_handler(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only for Owner.")
        return

    code = " ".join(context.args)
    if not code:
        await update.message.reply_text("Usage: /eval <code>")
        return

    try:
        result = eval(code)
        if asyncio.iscoroutine(result):
            result = await result
        await update.message.reply_text(f"<b>Eval Result:</b>\n<code>{result}</code>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"<b>Error:</b> <code>{str(e)}</code>", parse_mode="HTML")

# Register Handlers
application.add_handler(CommandHandler("broadcat", broadcast))
application.add_handler(CommandHandler("evanl", eval_handler))
