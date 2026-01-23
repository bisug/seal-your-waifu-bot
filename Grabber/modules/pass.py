from pyrogram import filters, types, enums
from Grabber import user_collection, app

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
@app.on_message(filters.command("pass"))
async def view_pass(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await message.reply_text("You don't have a profile yet. Start playing to generate one.")
        return

    pass_type = user.get("pass_type", "free")
    xp = user.get("xp", 0)
    level_num = get_level_from_xp(xp)

    status = f"🎫 **Pass:** {pass_type.capitalize()}\n⭐ **Level:** {level_num}\n⚡ **XP:** {xp}"
    await message.reply_text(status, parse_mode=enums.ParseMode.MARKDOWN)

# /buypass command
@app.on_message(filters.command("buypass"))
async def buy_pass(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    if user and user.get("pass_type") == "premium":
        await message.reply_text("✅ You already own a Premium Pass!")
        return

    if not user or user.get("balance", 0) < PREMIUM_PRICE:
        await message.reply_text(f"❌ You don’t have enough coins. Premium Pass costs {PREMIUM_PRICE} coins.")
        return

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"pass_type": "premium"}, "$inc": {"balance": -PREMIUM_PRICE}},
        upsert=True
    )

    await message.reply_text("🎉 Congratulations! You've successfully purchased the Premium Pass!")

# /claimpass command
@app.on_message(filters.command("claimpass"))
async def claim_pass_reward(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await message.reply_text("You don’t have a profile yet.")
        return

    pass_type = user.get("pass_type", "free")

    if user.get("pass_claimed"):
        await message.reply_text("❌ You have already claimed your pass reward.")
        return

    reward = PASS_REWARDS[pass_type]
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": reward}, "$set": {"pass_claimed": True}},
        upsert=True
    )

    await message.reply_text(f"🎁 You've claimed your {pass_type.capitalize()} Pass reward of {reward} coins!")

# /level command
@app.on_message(filters.command("level"))
async def level_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    if not user:
        await message.reply_text("No profile found. Start playing to gain XP!")
        return

    xp = user.get("xp", 0)
    level_num = get_level_from_xp(xp)
    required = 100 * (level_num + 1)
    
    # Calculate progress within current level
    previous_levels_xp = sum([100 * (i + 1) for i in range(level_num)])
    progress = xp - previous_levels_xp

    await message.reply_text(
        f"⭐ **Level:** {level_num}\n⚡ **XP:** {xp} / Next: {progress}/{required}",
        parse_mode=enums.ParseMode.MARKDOWN
    )
