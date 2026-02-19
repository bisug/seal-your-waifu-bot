import httpx
from pyrogram import filters, types, enums
from Grabber import app, user_collection, LOGGER
from config import config

           
EXTOL_API_KEY =""

                                               
async def get_extol_balance(api_key):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://marketapi.animerealms.org/api/balance",
            headers={"api-key": api_key},
            timeout=30
        )
        return resp.json()

                                          
async def transfer_extol(amount, to_address):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://marketapi.animerealms.org/api/transfer",
            headers={"api-key": EXTOL_API_KEY},
            params={"amount": amount, "to": to_address},
            timeout=30
        )
        return resp.json()

                        
@app.on_message(filters.command("tr"))
async def transfer_command(_, message: types.Message):
    if len(message.command) != 3:
        await message.reply_text("❌ Usage: `/tr <amount> <user_id>`", parse_mode=enums.ParseMode.MARKDOWN)
        return

    try:
        amount = float(message.command[1])
        target_id = int(message.command[2])
    except ValueError:
        await message.reply_text("❌ Invalid input format. Amount must be a number and User ID must be an integer.")
        return

    receiver = await user_collection.find_one({"id": target_id})

    if not receiver or "extol_key" not in receiver:
        await message.reply_text("❌ Target user is not registered or missing Extol key.")
        return

                                
    try:
        recv_data = await get_extol_balance(receiver["extol_key"])
        receiver_address = recv_data.get("address")
    except Exception as e:
        LOGGER.error(f"Error fetching extol address: {e}")
        await message.reply_text("❌ Connection to Extol API failed.")
        return

    if not receiver_address:
        await message.reply_text("❌ Could not fetch receiver's Extol address.")
        return

                      
    try:
        result = await transfer_extol(amount, receiver_address)
    except Exception as e:
        LOGGER.error(f"Error transferring extol: {e}")
        await message.reply_text("❌ Transfer failed due to API connection error.")
        return

    if result.get("ok"):
        await message.reply_text(
            f"✅ Sent **{amount} EXT** to user `{target_id}` successfully.",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(f"❌ Transfer failed: {result.get('error', 'Unknown error')}")
