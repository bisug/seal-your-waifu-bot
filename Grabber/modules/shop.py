from pyrogram import filters, types, enums
from Grabber import app, user_collection, OWNER_ID, sudo_users

AUTHORIZED_CONSOLES = set(sudo_users + [OWNER_ID])

@app.on_message(filters.command("givecoin"))
async def give_coin(_, message: types.Message) -> None:
    if message.from_user.id not in AUTHORIZED_CONSOLES:
        await message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        if len(message.command) < 2:
            raise ValueError
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await message.reply_text("❌ Invalid amount! Use: `/givecoin <amount>`", parse_mode=enums.ParseMode.MARKDOWN)
        return

    user_id = message.from_user.id
    
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    user_data = await user_collection.find_one({"id": user_id}, {"balance": 1})
    new_balance = user_data.get("balance", 0)

    await message.reply_text(f"✅ {amount} coins added!\n💰 **New Balance:** {new_balance} coins.", parse_mode=enums.ParseMode.MARKDOWN)
