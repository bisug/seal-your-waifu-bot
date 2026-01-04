import asyncio
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# Assuming these are already imported from Grabber
from Grabber import Grabberu as app
from Grabber import user_collection, collection # adjust if name is different

# ==========================================
#               CONFIGURATION
# ==========================================

SUPPORT_GROUP_ID = -1002429397912
OWNER_ID = 6574393060
MAX_ACTIVE_GAMES = 120

# In-memory active games (chat_id → game data)
active_games = {}  # {"character": dict, "guessed": bool}

# ==========================================
#               HELPERS
# ==========================================

async def get_user_balance(user_id: int) -> int:
    user = await user_collection.find_one({"id": user_id}, {"balance": 1})
    return user["balance"] if user and "balance" in user else 0


async def add_coins(user_id: int, amount: int):
    if amount <= 0:
        return
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )


# ==========================================
#               COMMANDS
# ==========================================

@app.on_message(filters.command(["balance", "bal"]))
async def balance_cmd(client, msg: Message):
    bal = await get_user_balance(msg.from_user.id)
    await msg.reply(f"Your balance: 💵 **{bal}** coins")


@app.on_message(filters.command("pay") & filters.reply)
async def pay_cmd(client, msg: Message):
    try:
        amount = int(msg.command[1])
    except (IndexError, ValueError):
        return await msg.reply("Usage: /pay <amount>  (reply to user)")

    if amount <= 0:
        return await msg.reply("Amount must be positive!")

    sender_id = msg.from_user.id
    recipient_id = msg.reply_to_message.from_user.id

    sender_bal = await get_user_balance(sender_id)
    if sender_bal < amount:
        return await msg.reply("Insufficient balance 😔")

    await user_collection.bulk_write([
        {
            "updateOne": {
                "filter": {"id": sender_id},
                "update": {"$inc": {"balance": -amount}}
            }
        },
        {
            "updateOne": {
                "filter": {"id": recipient_id},
                "update": {"$inc": {"balance": amount}},
                "upsert": True
            }
        }
    ])

    new_bal = await get_user_balance(sender_id)
    username = msg.reply_to_message.from_user.username
    mention = f"@{username}" if username else msg.reply_to_message.from_user.mention

    await msg.reply(f"💸 Paid **{amount}** coins to {mention}!\nYour balance: **{new_bal}**")


@app.on_message(filters.command("daily"))
async def daily_reward(client, msg: Message):
    user_id = msg.from_user.id
    user = await user_collection.find_one(
        {"id": user_id},
        {"last_daily_reward": 1}
    )

    today = datetime.utcnow().date()
    if user and user.get("last_daily_reward") and user["last_daily_reward"].date() == today:
        return await msg.reply("You've already claimed your daily reward today 🌞")

    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": 150}, "$set": {"last_daily_reward": datetime.utcnow()}},
        upsert=True
    )
    await msg.reply("🎉 **Daily reward claimed!** +150 coins")


@app.on_message(filters.command("weekly"))
async def weekly_bonus(client, msg: Message):
    user_id = msg.from_user.id
    user = await user_collection.find_one(
        {"id": user_id},
        {"last_weekly_bonus": 1}
    )

    if user and user.get("last_weekly_bonus"):
        if (datetime.utcnow() - user["last_weekly_bonus"]).days < 7:
            return await msg.reply("You've already claimed your weekly bonus this week ⏳")

    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": 750}, "$set": {"last_weekly_bonus": datetime.utcnow()}},
        upsert=True
    )
    await msg.reply("🎁 **Weekly bonus claimed!** +750 coins")


@app.on_message(filters.command("bonus"))
async def one_time_bonus(client, msg: Message):
    user_id = msg.from_user.id
    user = await user_collection.find_one({"id": user_id}, {"bonus_claimed": 1})

    if user and user.get("bonus_claimed"):
        return await msg.reply("❌ You have **already claimed** the one-time bonus!")

    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": 3000}, "$set": {"bonus_claimed": True}},
        upsert=True
    )
    await msg.reply("✨ **One-time bonus claimed!** +3000 coins")


@app.on_message(filters.command("mtop"))
async def money_top(client, msg: Message):
    top_users = await user_collection.find(
        {},
        {"id": 1, "first_name": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(10)

    if not top_users:
        return await msg.reply("No users with balance yet.")

    lines = []
    for i, u in enumerate(top_users, 1):
        name = u.get("first_name", "Unknown")
        bal = u.get("balance", 0)
        lines.append(f"{i}. <a href='tg://user?id={u['id']}'>{name}</a> — 💵 {bal}")

    text = "🏆 **TOP 10 RICHEST USERS**\n\n" + "\n".join(lines)
    await msg.reply_photo(
        photo="https://telegra.ph/file/8fce79d744297133b79b6.jpg",
        caption=text,
        parse_mode="html"
    )


@app.on_message(filters.command("nguess") & filters.chat(SUPPORT_GROUP_ID))
async def new_guess(client, msg: Message):
    chat_id = msg.chat.id

    if len(active_games) >= MAX_ACTIVE_GAMES:
        return await msg.reply("⚠️ Too many active games! Please wait...")

    # Get random character
    cursor = characters_collection.aggregate([{"$sample": {"size": 1}}])
    char_doc = await cursor.to_list(1)

    if not char_doc:
        return await msg.reply("No characters found in database 😢")

    character = char_doc[0]
    active_games[chat_id] = {
        "character": character,
        "guessed": False
    }

    await msg.reply_photo(
        photo=character["img_url"],
        caption="✨ **Guess this Waifu!** 🧐✨\nSend the name in chat!"
    )


# Fixed version - correct filter combination
@app.on_message(
    filters.text &
    ~filters.command &
    filters.chat(SUPPORT_GROUP_ID)
)
async def handle_guess(client, msg: Message):
    chat_id = msg.chat.id
    
    if chat_id not in active_games:
        return

    game = active_games[chat_id]
    if game["guessed"]:
        return

    guess = msg.text.strip().lower()
    character_name = game["character"]["name"].strip().lower()

    correct_words = set(character_name.split())
    guess_words = {w for w in guess.split() if len(w) > 1}

    if correct_words & guess_words:
        game["guessed"] = True
        await add_coins(msg.from_user.id, 100)
        
        await msg.reply(
            f"🎉 **Correct!** +100 coins for {msg.from_user.mention}"
        )

        # Small delay before new game
        await asyncio.sleep(1.2)
        
        # Start next round
        await new_guess(client, msg)
        
        # Clean up
        active_games.pop(chat_id, None)


@app.on_message(filters.command("name") & filters.reply & filters.chat(SUPPORT_GROUP_ID))
async def show_name(client, msg: Message):
    if not msg.reply_to_message or not msg.reply_to_message.photo:
        return

    chat_id = msg.chat.id
    if chat_id not in active_games:
        return

    name = active_games[chat_id]["character"]["name"]
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Copy Name", switch_inline_query_current_chat=name)
    ]])

    await msg.reply(
        f"**Character Name:**\n`{name}`",
        reply_markup=markup,
        parse_mode="markdown"
    )


# If you need to run the bot manually (optional)
# if __name__ == "__main__":
#     print("Bot is running...")
#     app.run()
