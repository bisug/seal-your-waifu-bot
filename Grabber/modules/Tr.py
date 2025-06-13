import logging
import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from Grabber import application, user_collection  # MongoDB initialized elsewhere

# Constants
EXTOL_API_KEY = ""

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Extol balance (used for receiver address)
async def get_extol_balance(api_key):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://marketapi.animerealms.org/api/balance",
            headers={"api-key": api_key}
        ) as resp:
            return await resp.json()

# Transfer Extols using the static API key
async def transfer_extol(amount, to_address):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://marketapi.animerealms.org/api/transfer",
            headers={"api-key": EXTOL_API_KEY},
            params={"amount": amount, "to": to_address}
        ) as resp:
            return await resp.json()

# /tr <amount> <user_id>
async def transfer_command(update: Update, context: CallbackContext):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /tr <amount> <user_id>")
        return

    try:
        amount = float(context.args[0])
        target_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid input format.")
        return

    receiver = await user_collection.find_one({"id": target_id})

    if not receiver or "extol_key" not in receiver:
        await update.message.reply_text("❌ Target user is not registered or missing Extol key.")
        return

    # Get receiver Extol address
    recv_data = await get_extol_balance(receiver["extol_key"])
    receiver_address = recv_data.get("address")

    if not receiver_address:
        await update.message.reply_text("❌ Could not fetch receiver's Extol address.")
        return

    # Perform transfer
    result = await transfer_extol(amount, receiver_address)

    if result.get("ok"):
        await update.message.reply_text(
            f"✅ Sent {amount} EXT to user `{target_id}` successfully.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Transfer failed: {result.get('error', 'Unknown error')}")

# Register command
application.add_handler(CommandHandler("tr", transfer_command))
