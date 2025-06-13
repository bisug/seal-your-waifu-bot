import logging
import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, user_collection  # your initialized MongoDB and bot app

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 📦 Function to fetch Extol balance to get receiver's address
async def get_extol_balance(api_key):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://marketapi.animerealms.org/api/balance",
            headers={"api-key": api_key}
        ) as resp:
            return await resp.json()

# 💸 Function to perform Extol transfer
async def transfer_extol(api_key, amount, to_address):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://marketapi.animerealms.org/api/transfer",
            headers={"api-key": api_key},
            params={"amount": amount, "to": to_address}
        ) as resp:
            return await resp.json()

# 📤 /tr <amount> <target_user_id>
async def transfer_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /tr <amount> <target_user_id>")
        return

    try:
        amount = float(context.args[0])
        target_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount or target user ID.")
        return

    # Get both sender and receiver info
    sender = await user_collection.find_one({"id": user_id})
    receiver = await user_collection.find_one({"id": target_id})

    if not sender or "extol_key" not in sender:
        await update.message.reply_text("❌ You are not registered or missing Extol key.")
        return

    if not receiver or "extol_key" not in receiver:
        await update.message.reply_text("❌ Target user not registered or missing Extol key.")
        return

    # Get receiver's Extol address
    recv_data = await get_extol_balance(receiver["extol_key"])
    receiver_address = recv_data.get("address")

    if not receiver_address:
        await update.message.reply_text("❌ Could not retrieve receiver's Extol address.")
        return

    # Execute transfer
    result = await transfer_extol(sender["extol_key"], amount, receiver_address)

    if result.get("ok"):
        await update.message.reply_text(
            f"✅ Transferred {amount} EXT to user `{target_id}` successfully.",
            parse_mode="Markdown"
        )
    else:
        error_msg = result.get("error", "unknown error")
        await update.message.reply_text(f"❌ Transfer failed: {error_msg}")

# 📌 Register the command handler
application.add_handler(CommandHandler("tr", transfer_command))
