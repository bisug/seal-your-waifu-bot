import random
import asyncio
from datetime import datetime, timezone
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import collection, user_collection
from Grabber.core.user import get_user_data, add_char_to_user, update_user
from Grabber.core.game import update_user_balance

# Constants provided by user (adapted for new logic)
start_messages = [
    "✨ Finally the time has come ✨",
    "💫 The moment you've been waiting for 💫",
    "🌟 The stars align for this proposal 🌟"
]
rejection_captions = [
    "She slapped you and ran away😂",
    "She rejected you outright! 😂",
    "You got a harsh 'NO!' 😂"
]
# Using user provided images
acceptance_images = [
    "https://te.legra.ph/file/4fe133737bee4866a3549.png",
    "https://te.legra.ph/file/28d46e4656ee2c3e7dd8f.png",
    "https://te.legra.ph/file/d32c6328c6d271dd00816.png"
]
rejection_images = [
    "https://te.legra.ph/file/d6e784e5cda62ac27541f.png",
    "https://te.legra.ph/file/e4e1ba60b4e79359bf9e7.png",
    "https://te.legra.ph/file/81d011398da3a6f49fa7f.png"
]

# Rarity weights for character reward (reused from daily.py logic)
RARITY_WEIGHTS = {
    '⚪ Common': 60,
    '🟢 Medium': 30,
    '🟠 Rare': 9,
    '🟡 Legendary': 1
}

async def get_random_waifu():
    rarity = random.choices(list(RARITY_WEIGHTS.keys()), weights=RARITY_WEIGHTS.values(), k=1)[0]
    cursor = collection.aggregate([{'$match': {'rarity': rarity}}, {'$sample': {'size': 1}}])
    res = await cursor.to_list(length=1)
    return res[0] if res else None

@app.on_message(filters.command("propose"))
async def propose_command(_, message: types.Message):
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    
    # Check Daily Limit
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user and user.get('last_propose_date') == now_date:
        return await message.reply_text("⏳ You have already proposed today! Come back tomorrow.")

    # Send initial message
    start_msg = random.choice(start_messages)
    roll_text = random.choice(["Proposing her....💍", "Getting down on one knee....💍", "Popping the question....💍"])
    
    # Send initial UI/animation
    await message.reply_text(f"{start_msg}\n\n{roll_text}")
    await asyncio.sleep(2) # Suspense

    # Calculate Outcome
    # 0-3: Character (3%)
    # 3-13: 2000 Shards (10%)
    # 13-43: 500 Shards (30%)
    # 43-100: Rejection (57%)
    roll = random.uniform(0, 100)

    if roll < 3:
        # Win Character
        char = await get_random_waifu()
        if char:
            await add_char_to_user(user_id, char)
            caption = (
                f"💍 **Proposal Accepted!** 💍\n\n"
                f"<b>{char['name']}</b> has accepted your proposal! 😇\n"
                f"Slave Name: {char['name']}\n"
                f"Rarity: {char['rarity']}\n"
                f"Anime: {char['anime']}"
            )
            img_url = char['img_url']
            await message.reply_photo(photo=img_url, caption=caption)
        else:
            # Fallback if no char found (unlikely)
            await update_user_balance(user_id, 2000)
            await message.reply_text("💍 **Proposal Accepted!**\nHowever, she was too shy to appear. You found 2000 Shards instead!")

    elif roll < 13:
        # Win 2000 Shards
        await update_user_balance(user_id, 2000)
        img = random.choice(acceptance_images)
        await message.reply_photo(photo=img, caption="💍 **Proposal Accepted!**\nShe was flattered but busy. She sent you **2,000 Shards** as a gift!")

    elif roll < 43:
        # Win 500 Shards
        await update_user_balance(user_id, 500)
        img = random.choice(acceptance_images)
        await message.reply_photo(photo=img, caption="💍 **Proposal Accepted!**\nShe smiled and gave you **500 Shards** for your effort!")

    else:
        # Rejection
        img = random.choice(rejection_images)
        caption = random.choice(rejection_captions)
        await message.reply_photo(photo=img, caption=f"💔 **Rejection!**\n{caption}")

    # Mark as done for today
    await update_user(user_id, {"$set": {"last_propose_date": now_date}})



