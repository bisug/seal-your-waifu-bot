import asyncio
import random
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Assuming these are already defined and exported from Grabber
from Grabber import user_collection, collection
from Grabber import Grabberu as app
SUPPORT_GROUP_ID = -1002429397912
OWNER_ID = 6574393060

MAX_ACTIVE_GAMES = 100
current_characters = {}  # chat_id: {"character": dict, "guessed": bool}

# ==================== HELPERS ====================

async def add_coins(user_id: int, amount: int):
    if amount <= 0:
        return
    
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

# ==================== COMMANDS ====================

@app.on_message(filters.command(["balance", "bal"]))
async def balance_cmd(_, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one(
        {"id": user_id},
        {"balance": 1}
    )
    balance_amount = user_data.get("balance", 0) if user_data else 0
    await message.reply(f"Your balance: 💵 **{balance_amount}** coins")


@app.on_message(filters.command("pay") & filters.reply)
async def pay_cmd(_, message: Message):
    sender_id = message.from_user.id
    recipient = message.reply_to_message.from_user
    recipient_id = recipient.id

    try:
        amount = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("Usage: /pay <amount> (reply to user)")

    if amount <= 0:
        return await message.reply("Amount must be positive!")

    sender_data = await user_collection.find_one(
        {"id": sender_id},
        {"balance": 1}
    )
    
    if not sender_data or sender_data.get("balance", 0) < amount:
        return await message.reply("Insufficient balance!")

    # Atomic bulk operation
    await user_collection.bulk_write([
        {"updateOne": {
            "filter": {"id": sender_id},
            "update": {"$inc": {"balance": -amount}}
        }},
        {"updateOne": {
            "filter": {"id": recipient_id},
            "update": {"$inc": {"balance": amount}},
            "upsert": True
        }}
    ])

    new_balance = await user_collection.find_one(
        {"id": sender_id},
        {"balance": 1}
    )

    mention = f"@{recipient.username}" if recipient.username else recipient.mention
    await message.reply(
        f"💵 Payment successful! You paid **{amount}** coins to {mention}\n"
        f"Your balance: 💵 **{new_balance.get('balance', 0)}** coins"
    )


@app.on_message(filters.command("daily"))
async def daily_reward_cmd(_, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one(
        {"id": user_id},
        {"last_daily_reward": 1}
    )

    today = datetime.utcnow().date()
    if user_data and user_data.get("last_daily_reward"):
        if user_data["last_daily_reward"].date() == today:
            return await message.reply("You've already claimed your daily reward today!")

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": 150},
            "$set": {"last_daily_reward": datetime.utcnow()}
        },
        upsert=True
    )
    await message.reply("🎉 You've claimed your daily reward of **150 coins**!")


@app.on_message(filters.command("weekly"))
async def weekly_bonus_cmd(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one(
        {"id": user_id},
        {"last_weekly_bonus": 1}
    )

    if user and user.get("last_weekly_bonus"):
        if (datetime.utcnow() - user["last_weekly_bonus"]).days < 7:
            return await message.reply("You've already claimed your weekly bonus this week!")

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": 750},
            "$set": {"last_weekly_bonus": datetime.utcnow()}
        },
        upsert=True
    )
    await message.reply("🎉 You've claimed your **weekly bonus** of **750 coins**!")


@app.on_message(filters.command("bonus"))
async def one_time_bonus_cmd(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one(
        {"id": user_id},
        {"bonus_claimed": 1}
    )

    if user and user.get("bonus_claimed"):
        return await message.reply("❌ You have **already claimed** this one-time bonus!")

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": 3000},
            "$set": {"bonus_claimed": True}
        },
        upsert=True
    )
    await message.reply("🎁 You've claimed your **one-time bonus** of **3000 coins**!")


@app.on_message(filters.command("mtop"))
async def mtop_cmd(_, message: Message):
    top_users = await user_collection.find(
        {},
        {"id": 1, "first_name": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(length=10)

    if not top_users:
        return await message.reply("No users in leaderboard yet.")

    lines = []
    for i, user in enumerate(top_users, 1):
        name = user.get("first_name", "Unknown")
        uid = user.get("id")
        balance = user.get("balance", 0)
        lines.append(f"{i}. <a href='tg://user?id={uid}'>{name}</a> - 💵 {balance}")

    text = "🏆 **Top 10 Users with Highest Balance:**\n\n" + "\n".join(lines)

    await message.reply_photo(
        photo="https://telegra.ph/file/8fce79d744297133b79b6.jpg",
        caption=text,
        parse_mode="html"
    )


@app.on_message(filters.command("nguess") & filters.chat(SUPPORT_GROUP_ID))
async def nguess_cmd(_, message: Message):
    chat_id = message.chat.id

    if len(current_characters) >= MAX_ACTIVE_GAMES:
        return await message.reply("⚠️ Too many active waifu games! Wait for others to finish.")

    result = await collection.aggregate([{"$sample": {"size": 1}}]).to_list(1)
    if not result:
        return await message.reply("No waifus found in the database.")

    character = result[0]
    current_characters[chat_id] = {
        "character": character,
        "guessed": False
    }

    await message.reply_photo(
        photo=character["img_url"],
        caption="✨ **Guess this Waifu!** 🧐✨\nJust send the name!"
    )


@app.on_message(filters.text & ~filters.command & filters.chat(SUPPORT_GROUP_ID))
async def handle_guess(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in current_characters:
        return

    game = current_characters[chat_id]
    if game["guessed"]:
        return

    guess = message.text.strip().lower()
    character_name = game["character"]["name"].strip().lower()

    correct_words = set(character_name.split())
    guess_words = set(word for word in guess.split() if len(word) > 1)

    if correct_words & guess_words:
        game["guessed"] = True
        await add_coins(message.from_user.id, 100)
        await message.reply(f"🎉 **Correct!** You earned **100 coins**!")

        del current_characters[chat_id]
        await asyncio.sleep(1)  # small delay
        await nguess_cmd(_, message)  # start new round


@app.on_message(filters.command("name") & filters.reply & filters.chat(SUPPORT_GROUP_ID))
async def name_cmd(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return

    chat_id = message.chat.id
    if chat_id not in current_characters:
        return

    char_name = current_characters[chat_id]["character"]["name"]
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Copy Name", switch_inline_query_current_chat=char_name)
    ]])

    await message.reply(
        f"📜 **Character Name:**\n`{char_name}`",
        reply_markup=markup,
        parse_mode="markdown"
    )


# Optional: bot startup message (you can remove if not needed)
print("Balance & Waifu Guess module loaded successfully")
