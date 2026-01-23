import asyncio
import random
import time
from pyrogram import filters, types, enums
from Grabber import user_collection, collection, app

# Rarity chances
RARITY_CHANCES = {
    "🫧 Royal": 1,
    "🔮 Limited Edition": 5,
    "💮 Exclusive": 10,
    "💠 Cosmic": 15,
    "🟡 Legendary": 20,
    "🟠 Rare": 25,
    "🟢 Medium": 24
}

# Default pet
DEFAULT_PET = {"name": "Fluffy", "luck": 1.0, "owned": True}

# Cooldown tracker
hunt_cooldowns = {}

def is_on_cooldown(user_id):
    now = time.time()
    if user_id in hunt_cooldowns:
        diff = now - hunt_cooldowns[user_id]
        if diff < 60:
            return True, int(60 - diff)
    hunt_cooldowns[user_id] = now
    return False, 0

@app.on_message(filters.command("hunt"))
async def hunt_cmd(_, message: types.Message):
    user_id = message.from_user.id
    cooldown_active, seconds_left = is_on_cooldown(user_id)

    if cooldown_active:
        await message.reply_text(f"⏳ Please wait {seconds_left}s before hunting again.")
        return

    user = await user_collection.find_one({"id": user_id}) or {}
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", "Fluffy")
    pet = next((p for p in pets if p["name"] == current), DEFAULT_PET)
    luck = pet.get("luck", 1.0)

    msg = await message.reply_text(f"🦊 {pet['name']} is going hunting...")
    await asyncio.sleep(1)
    await msg.edit_text("🌲 Searching the forest...")
    await asyncio.sleep(1)

    coins = random.randint(100, 300)
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": coins}}, upsert=True)

    egg_chance = 5 * luck
    roll = random.uniform(0, 100)

    if roll <= egg_chance:
        egg_id = f"egg_{random.randint(1000, 9999)}"
        await user_collection.update_one({"id": user_id}, {"$push": {"eggs": egg_id}}, upsert=True)
        await msg.edit_text(f"🥚 {pet['name']} found a mysterious egg!\n💰 Also brought back {coins} coins!")
    else:
        await msg.edit_text(f"💰 {pet['name']} brought back {coins} coins from the hunt!")

@app.on_message(filters.command("hatch"))
async def hatch_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}

    eggs = user.get("eggs", [])
    if not eggs:
        await message.reply_text("❌ You don’t have any eggs to hatch!")
        return

    egg = eggs[0]
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": egg}}, upsert=True)

    msg = await message.reply_text("🥚 Hatching your egg...")
    await asyncio.sleep(1)
    await msg.edit_text("✨ Magic is in the air...")
    await asyncio.sleep(1)

    roll = random.randint(1, 100)
    total = 0
    selected_rarity = "🟢 Medium"
    for rarity, chance in RARITY_CHANCES.items():
        total += chance
        if roll <= total:
            selected_rarity = rarity
            break

    waifus = await collection.find({"rarity": selected_rarity}).to_list(length=None)
    if waifus:
        character = random.choice(waifus)
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
        await msg.edit_text("🎉 Success! Sending details...")
        await message.reply_photo(
            photo=character["img_url"],
            caption=f"You hatched a {selected_rarity} waifu!\n\n"
                    f"**Name:** {character['name']}\n"
                    f"**Anime:** {character['anime']}",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await msg.edit_text("❌ The egg was empty... That's unlucky.")

@app.on_message(filters.command("eggs"))
async def eggs_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}
    egg_count = len(user.get("eggs", []))
    await message.reply_text(f"🥚 You have **{egg_count}** eggs.", parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("claimegg"))
async def claimegg_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}

    if user.get("claimed_egg", False):
        await message.reply_text("❌ You've already claimed your free egg.")
        return

    egg_id = f"egg_{random.randint(1000, 9999)}"
    await user_collection.update_one({"id": user_id}, {
        "$push": {"eggs": egg_id},
        "$set": {"claimed_egg": True}
    }, upsert=True)

    await message.reply_text("✅ You claimed 1 free egg! Use /hatch to open it.")
