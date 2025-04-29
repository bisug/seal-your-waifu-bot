import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from Grabber import user_collection, collection, application

# Constants
PREMIUM_PRICE = 500000

# Rewards Config
PASS_REWARDS = {
    "free": 500,
    "premium": 2000
}

# Levels config
LEVEL_CAP = 50


# XP-based Level Calculation
def get_level_from_xp(xp: int) -> int:
    level = 0
    required_xp = 100
    while xp >= required_xp and level < LEVEL_CAP:
        xp -= required_xp
        level += 1
        required_xp = 100 * (level + 1)
    return level


# /pass command to view status
async def view_pass(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await update.message.reply_text("You don't have a profile yet. Start playing to generate one.")
        return

    pass_type = user.get("pass_type", "free")
    xp = user.get("xp", 0)
    level = get_level_from_xp(xp)

    status = f"🎫 Pass: {pass_type.capitalize()}\n⭐ Level: {level}\n⚡ XP: {xp}"
    await update.message.reply_text(status)


# /buypass command
async def buy_pass(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})

    if user and user.get("pass_type") == "premium":
        await update.message.reply_text("✅ You already own a Premium Pass!")
        return

    if not user or user.get("balance", 0) < PREMIUM_PRICE:
        await update.message.reply_text("❌ You don’t have enough coins. Premium Pass costs 500000 coins.")
        return

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"pass_type": "premium"}, "$inc": {"balance": -PREMIUM_PRICE}},
        upsert=True
    )

    await update.message.reply_text("🎉 Congratulations! You've successfully purchased the Premium Pass!")


# /claimpass command
async def claim_pass_reward(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await update.message.reply_text("You don’t have a profile yet.")
        return

    pass_type = user.get("pass_type", "free")

    if user.get("pass_claimed"):
        await update.message.reply_text("❌ You have already claimed your pass reward.")
        return

    reward = PASS_REWARDS[pass_type]
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": reward}, "$set": {"pass_claimed": True}},
        upsert=True
    )

    await update.message.reply_text(f"🎁 You've claimed your {pass_type.capitalize()} Pass reward of {reward} coins!")


# /level command
async def level(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await update.message.reply_text("No profile found. Start playing to gain XP!")
        return

    xp = user.get("xp", 0)
    level = get_level_from_xp(xp)
    required = 100 * (level + 1)
    progress = xp - sum([100 * (i + 1) for i in range(level)])

    await update.message.reply_text(
        f"⭐ Level: {level}\n⚡ XP: {xp} / Next: {progress}/{required}"
    )


# Handler registration
application.add_handler(CommandHandler("pass", view_pass))
application.add_handler(CommandHandler("buypass", buy_pass))
application.add_handler(CommandHandler("claimpass", claim_pass_reward))
application.add_handler(CommandHandler("level", level))
  
