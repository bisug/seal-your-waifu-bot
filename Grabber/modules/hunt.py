import asyncio
import random
import time
from datetime import datetime, timedelta
from pyrogram import filters, types, enums
from Grabber import user_collection, collection, app
from Grabber.core.user import add_pet_xp
from Grabber.core.progression import add_xp
from Grabber.modules.quests import update_quest_progress

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
        
        # Update egg quest
        await update_quest_progress(user_id, "egg_hunter", 1)

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
    await show_egg_page(message, 0, message.from_user.id)

async def show_egg_page(message_or_query, page: int, user_id: int):
    """Display egg inventory with interactive buttons."""
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if not eggs:
        text = "❌ <b>No eggs found!</b>\n\nUse <code>/hunt</code> to find eggs."
        if isinstance(message_or_query, types.CallbackQuery):
            try:
                await message_or_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
            except:
                pass
        else:
            await message_or_query.reply_text(text, parse_mode=enums.ParseMode.HTML)
        return
    
    # Pagination
    page = page % len(eggs)
    egg = eggs[page]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    status = egg.get("status", "fresh")
    
    # Determine action button
    action_button = None
    status_display = ""
    
    if status == "fresh":
        status_display = f"🛑 <b>Status:</b> Not incubated\n⏱️ <b>Required:</b> {tier_info['wait_min']} minutes"
        action_button = types.InlineKeyboardButton("🌡️ Start Incubation", callback_data=f"egg_incubate:{page}")
    elif status == "incubating":
        hatch_time = egg.get("hatch_time")
        if hatch_time and datetime.now() < hatch_time:
            remaining = hatch_time - datetime.now()
            mins_left = int(remaining.total_seconds() / 60)
            status_display = f"⏳ <b>Status:</b> Incubating\n⏱️ <b>Time Left:</b> {mins_left} minutes"
            action_button = types.InlineKeyboardButton("⏳ Incubating...", callback_data="egg_wait")
        else:
            status_display = "✅ <b>Status:</b> Ready to hatch!"
            action_button = types.InlineKeyboardButton("🎁 Hatch Now!", callback_data=f"egg_hatch:{page}")
    
    text = (
        f"🥚 <b>Egg Inventory</b>\n\n"
        f"<b>{egg.get('name', 'Unknown Egg')}</b>\n"
        f"{status_display}\n\n"
        f"<i>Egg {page + 1} of {len(eggs)}</i>"
    )
    
    # Build buttons
    buttons = []
    
    # Navigation row
    nav_row = []
    if len(eggs) > 1:
        nav_row.append(types.InlineKeyboardButton("⬅️", callback_data=f"egg_page:{page - 1}"))
        nav_row.append(types.InlineKeyboardButton(f"{page + 1}/{len(eggs)}", callback_data="egg_noop"))
        nav_row.append(types.InlineKeyboardButton("➡️", callback_data=f"egg_page:{page + 1}"))
        buttons.append(nav_row)
    
    # Action button
    if action_button:
        buttons.append([action_button])
    
    markup = types.InlineKeyboardMarkup(buttons) if buttons else None
    
    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
        else:
            await message_or_query.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Egg page error: {e}")

# Callback handlers
@app.on_callback_query(filters.regex(r"^egg_page:"))
async def egg_page_callback(_, query: types.CallbackQuery):
    page = int(query.data.split(":")[1])
    await show_egg_page(query, page, query.from_user.id)
    await query.answer()

@app.on_callback_query(filters.regex(r"^egg_incubate:"))
async def egg_incubate_callback(_, query: types.CallbackQuery):
    page = int(query.data.split(":")[1])
    user_id = query.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if page >= len(eggs):
        return await query.answer("❌ Egg not found!", show_alert=True)
    
    egg = eggs[page]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    
    # Check active pet for Caregiver skill
    pets = user.get("pets", [DEFAULT_PET])
    active_pet = next((p for p in pets if p["name"] == user.get("current_pet")), {})
    
    wait_min = tier_info["wait_min"]
    if active_pet.get("ability") == "Caregiver":
        wait_min = int(wait_min * 0.5)
    
    # Start incubation
    ready_time = datetime.now() + timedelta(minutes=wait_min)
    
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                f"eggs.{page}.status": "incubating",
                f"eggs.{page}.hatch_time": ready_time
            }
        }
    )
    
    await query.answer(f"🌡️ Incubation started! Come back in {wait_min} minutes.", show_alert=True)
    await show_egg_page(query, page, user_id)

@app.on_callback_query(filters.regex(r"^egg_hatch:"))
async def egg_hatch_callback(_, query: types.CallbackQuery):
    page = int(query.data.split(":")[1])
    user_id = query.from_user.id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if page >= len(eggs):
        return await query.answer("❌ Egg not found!", show_alert=True)
    
    egg = eggs[page]
    
    # Verify it's ready
    if egg.get("status") != "incubating":
        return await query.answer("❌ Egg is not incubating!", show_alert=True)
    
    ready_time = egg.get("hatch_time")
    if ready_time and datetime.now() < ready_time:
        remaining = int((ready_time - datetime.now()).total_seconds() / 60)
        return await query.answer(f"⏳ Still incubating! {remaining}m left.", show_alert=True)
    
    # Hatch the egg
    await crack_open_egg_inline(query, user_id, egg)

@app.on_callback_query(filters.regex(r"^egg_(wait|noop)$"))
async def egg_noop_callback(_, query: types.CallbackQuery):
    await query.answer()

async def crack_open_egg_inline(query: types.CallbackQuery, user_id: int, egg: dict):
    """Hatch an egg from the inline UI."""
    # Remove egg from inventory
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})
    
    await query.message.edit_text("🥚 <b>Cracking open...</b>", parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(2)
    
    # Corrupted logic
    if egg.get("is_corrupted", False):
        if random.random() < 0.5:
            await query.message.edit_text("💥 <b>The egg exploded!</b>\nIt was corrupted...", parse_mode=enums.ParseMode.HTML)
            return
        else:
            rarity = "🫧 Royal"
    else:
        rarity_pool = EGG_TIERS[egg["tier"]]["pool"]
        rarity = random.choice(rarity_pool)
    
    # Fetch character
    waifus = await collection.find({"rarity": rarity}).to_list(length=None)
    if waifus:
        character = random.choice(waifus)
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
        
        # Grant XP
        await add_xp(user_id, 15, "egg_hatch")
        
        await query.message.edit_text("🎉 <b>Success! Sending details...</b>", parse_mode=enums.ParseMode.HTML)
        await query.message.reply_photo(
            photo=character["img_url"],
            caption=(
                f"🐣 <b>Hatched Successfully!</b>\n\n"
                f"📛 <b>{character['name']}</b>\n"
                f"✨ <b>{rarity}</b>\n"
                f"🎬 {character['anime']}"
            ),
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.message.edit_text("⚠️ The egg was empty (DB error).", parse_mode=enums.ParseMode.HTML)

# Keep old /hatch command for backwards compatibility but redirect to new UI

@app.on_message(filters.command("hatch"))
async def hatch_cmd(_, message: types.Message):
    # Redirect to new interactive UI
    await show_egg_page(message, 0, message.from_user.id)

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
        
        # Grant XP for hatching
        await add_xp(user_id, 15, "egg_hatch")
        
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
