import asyncio
import random
import time
from datetime import datetime, timedelta
from pyrogram import filters, types, enums
from Grabber import user_collection, collection, app
from Grabber.core.user import add_pet_xp

# Egg Tiers & Properties
EGG_TIERS = {
    "common": {"name": "🥚 Common Egg", "chance": 70, "pool": ["🟢 Medium", "🟠 Rare"], "wait_min": 5},
    "gold":   {"name": "🌟 Golden Egg", "chance": 25, "pool": ["🟡 Legendary", "💠 Cosmic"], "wait_min": 30},
    "void":   {"name": "🌌 Void Egg",   "chance": 5,  "pool": ["💮 Exclusive", "🔮 Limited Edition"], "wait_min": 180}
}

# Risk Mechanic
CORRUPTED_EGG_CHANCE = 5 
# 5% chance any egg is actually corrupted (visualized as Void but risky)

DEFAULT_PET = {"name": "Fluffy Fox 🦊", "luck": 0.10, "level": 1, "xp": 0, "owned": True}
hunt_cooldowns = {}

def is_on_cooldown(user_id):
    now = time.time()
    if user_id in hunt_cooldowns:
        diff = now - hunt_cooldowns[user_id]
        limit = 60
        if diff < limit:
             return True, int(limit - diff)
    return False, 0

def get_egg_roll(luck_multiplier):
    """Roll for an egg rarity based on weighted probability."""
    roll = random.uniform(0, 100)
    
    # Luck boosts chance of better tiers slightly
    void_c = EGG_TIERS["void"]["chance"] * (1 + luck_multiplier)
    gold_c = EGG_TIERS["gold"]["chance"] * (1 + luck_multiplier)
    
    if roll <= void_c: return "void"
    if roll <= (void_c + gold_c): return "gold"
    return "common"

@app.on_message(filters.command("hunt"))
async def hunt_cmd(_, message: types.Message):
    user_id = message.from_user.id
    cooldown_active, seconds_left = is_on_cooldown(user_id)

    if cooldown_active:
        return await message.reply_text(f"⏳ Please wait {seconds_left}s before hunting again.")
    # Fetch User & Pet
    user = await user_collection.find_one({"id": user_id}) or {}
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])
    pet = next((p for p in pets if p["name"] == current), DEFAULT_PET)
    
    # Skill Check
    ability = pet.get("ability", None)
    luck = pet.get("luck", 0.1)
    
    # Cooldown Logic (Speedster)
    cooldown_time = 50 if ability == "Speedster" else 60
    
    # Re-verify cooldown with correct time (Simple patch)
    now = time.time()
    if user_id in hunt_cooldowns:
        if now - hunt_cooldowns[user_id] < cooldown_time:
             # Just return silently if they spam faster than their specific limit
             return 
             
    hunt_cooldowns[user_id] = now

    msg = await message.reply_text(f"🦊 <b>{pet['name']}</b> is going hunting...", parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(2)

    coins = random.randint(100, 300)
    
    # Skill: Scavenger (Double Coins)
    bonus_text = ""
    if ability == "Scavenger" and random.random() < 0.2:
        coins *= 2
        bonus_text += "\n💰 <b>Double Coins!</b> (Scavenger)"
        
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": coins}}, upsert=True)
    
    # XP Award
    xp_gain = random.randint(10, 20)
    if ability == "Beginner's Luck":
        xp_gain = int(xp_gain * 1.05)
    await add_pet_xp(user_id, pet["name"], xp_gain)

    # Egg Drop Logic
    base_drop_chance = 15 * (1 + luck) # Base 15% drop rate
    
    # Skill: Hoarder (Bonus Egg Chance)
    extra_drop = False
    if ability == "Hoarder" and random.random() < 0.05:
        extra_drop = True
    
    if random.uniform(0, 100) <= base_drop_chance or extra_drop:
        tier_key = get_egg_roll(luck)
        tier_data = EGG_TIERS[tier_key]
        
        # Determine if corrupted
        is_corrupted = random.uniform(0, 100) <= CORRUPTED_EGG_CHANCE
        
        egg_data = {
            "id": f"egg_{random.randint(10000, 99999)}",
            "tier": tier_key, 
            "name": tier_data["name"],
            "obtained_at": datetime.now(),
            "status": "fresh", # fresh -> incubating -> ready
            "is_corrupted": is_corrupted
        }
        
        await user_collection.update_one({"id": user_id}, {"$push": {"eggs": egg_data}}, upsert=True)
        if extra_drop:
            # Add a secondary common egg
            extra_egg = egg_data.copy()
            extra_egg["id"] = f"egg_{random.randint(10000, 99999)}"
            extra_egg["tier"] = "common"
            extra_egg["name"] = "🥚 Bonus Common Egg"
            await user_collection.update_one({"id": user_id}, {"$push": {"eggs": extra_egg}}, upsert=True)
            bonus_text += "\n🥚 <b>Bonus Egg Found!</b> (Hoarder)"

        await msg.edit_text(
            f"🎁 <b>Loot Found!</b>\n\n"
            f"🥚 <b>{tier_data['name']}</b> discovered!\n"
            f"💰 <b>+{coins} Coins</b>{bonus_text}\n"
            f"🆙 <b>+{xp_gain} XP</b> for {pet['name']}",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await msg.edit_text(
            f"🌲 <b>Hunt Complete!</b>\n\n"
            f"💰 <b>+{coins} Coins</b>{bonus_text}\n"
            f"🆙 <b>+{xp_gain} XP</b> for {pet['name']}\n"
            f"<i>No eggs found this time.</i>",
            parse_mode=enums.ParseMode.HTML
        )

@app.on_message(filters.command("eggs"))
async def eggs_cmd(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if not eggs:
        return await message.reply_text("❌ You have no eggs. Use /hunt to find some!")
        
    text = "<b>🥚 Your Egg Basket</b>\n\n"
    for i, egg in enumerate(eggs):
        tier = EGG_TIERS.get(egg.get("tier", "common"))
        status = egg.get("status", "fresh")
        
        status_text = "Free to hatch"
        if status == "incubating":
            hatch_time = egg.get("hatch_time")
            if hatch_time and datetime.now() < hatch_time:
                remaining = hatch_time - datetime.now()
                status_text = f"⏳ {int(remaining.total_seconds() / 60)}m left"
            else:
                status_text = "✅ Ready to open!"
        elif status == "fresh":
            status_text = f"🛑 Needs {tier['wait_min']}m incubation"
            
        text += f"<b>{i+1}. {egg.get('name', 'Unknown Egg')}</b>\n   └ {status_text}\n"
        
    text += "\nTo manage an egg, use: <code>/hatch &lt;number&gt;</code>"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("hatch"))
async def hatch_cmd(_, message: types.Message):
    try:
        index = int(message.command[1]) - 1
    except (IndexError, ValueError):
        return await message.reply_text("❌ Usage: <code>/hatch &lt;number&gt;</code> (Check /eggs)", parse_mode=enums.ParseMode.HTML)

    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])

    if index < 0 or index >= len(eggs):
        return await message.reply_text("❌ Invalid egg number.")

    egg = eggs[index]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    
    # State Machine: Fresh -> Incubating -> Ready
    if egg.get("status") == "fresh":
        # Check active pet for Caregiver skill
        pets = user.get("pets", [DEFAULT_PET])
        active_pet = next((p for p in pets if p["name"] == user.get("current_pet")), {})
        
        wait_min = tier_info["wait_min"]
        if active_pet.get("ability") == "Caregiver":
            wait_min = int(wait_min * 0.5)
            
        # Start Incubation
        wait_time = timedelta(minutes=wait_min)
        ready_time = datetime.now() + wait_time
        
        # Update specific egg in array
        await user_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    f"eggs.{index}.status": "incubating",
                    f"eggs.{index}.hatch_time": ready_time
                }
            }
        )
        return await message.reply_text(f"🌡️ <b>Incubation Started!</b>\nCome back in {wait_min} minutes.", parse_mode=enums.ParseMode.HTML)

    elif egg.get("status") == "incubating":
        ready_time = egg.get("hatch_time")
        if ready_time and datetime.now() < ready_time:
            remaining = int((ready_time - datetime.now()).total_seconds() / 60)
            return await message.reply_text(f"⏳ <b>Still Incubating!</b>\n{remaining} minutes remaining.", parse_mode=enums.ParseMode.HTML)
        
        # Ready to Hatch!
        await crack_open_egg(message, user_id, egg, index)

async def crack_open_egg(message, user_id, egg, index):
    # Consume Egg
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})
    
    msg = await message.reply_text("🥚 <b>Cracking open...</b>", parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(2)
    
    # Corrupted Logic
    if egg.get("is_corrupted", False):
        if random.random() < 0.5:
            await msg.edit_text("💥 <b>The egg exploded!</b>\nIt was corrupted... You got nothing.", parse_mode=enums.ParseMode.HTML)
            return
        else:
            # Jackpot
            rarity = "🫧 Royal" 
    else:
        # Standard Pool
        rarity_pool = EGG_TIERS[egg["tier"]]["pool"]
        rarity = random.choice(rarity_pool)

    # Fetch Character
    waifus = await collection.find({"rarity": rarity}).to_list(length=None)
    if waifus:
        character = random.choice(waifus)
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
        await msg.edit_text("🎉 Success! Sending details...")
        await message.reply_photo(
            photo=character["img_url"],
            caption=f"🐣 <b>Hatched Successfully!</b>\n\n"
                    f"📛 <b>{character['name']}</b>\n"
                    f"✨ <b>{rarity}</b>\n"
                    f"🎬 {character['anime']}",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await msg.edit_text("⚠️ The egg was empty (Database error: No chars for this rarity).")
