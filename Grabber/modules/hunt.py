import asyncio
import random
import time
from datetime import datetime, timedelta
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import md_escape
from Grabber import user_collection, collection, app
from Grabber.core.user import add_pet_xp
from Grabber.core.progression import add_xp
from Grabber.modules.quests import update_quest_progress
from Grabber.modules.achievements import check_achievements
from Grabber.modules.rarities import RARITY_MAP

                        
EGG_TIERS = {
    "common": {"name": "🥚 Common Egg", "chance": 70, "pool": [RARITY_MAP[4], RARITY_MAP[2]], "wait_min": 5},
    "gold":   {"name": "🌟 Golden Egg", "chance": 25, "pool": [RARITY_MAP[3], RARITY_MAP[5]], "wait_min": 30},
    "void":   {"name": "🌌 Void Egg",   "chance": 5,  "pool": [RARITY_MAP[6], RARITY_MAP[7]], "wait_min": 180}
}

               
CORRUPTED_EGG_CHANCE = 5 
                                                                        

from Grabber.modules.pet import DEFAULT_PET
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
                                                               
    roll = random.uniform(0, 100)
    
                                                 
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
        return await message.reply_text(f"⏳ Please wait {seconds_left}s before hunting again.", parse_mode=ParseMode.MARKDOWN_V2)
                      
    user = await user_collection.find_one({"id": user_id}) or {}
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])
    pet = next((p for p in pets if p["name"] == current), DEFAULT_PET)
    
                 
    ability = pet.get("ability", None)
    luck = pet.get("luck", 0.1)
    
                                
    cooldown_time = 50 if ability == "Speedster" else 60
    
                                                         
    now = time.time()
    if user_id in hunt_cooldowns:
        if now - hunt_cooldowns[user_id] < cooldown_time:
                                                                                 
             return 
             
    hunt_cooldowns[user_id] = now

    msg = await message.reply_text(f"🦊 **{md_escape(pet['name'])}** is going hunting...", parse_mode=ParseMode.MARKDOWN_V2)
    await asyncio.sleep(2)

    shards = random.randint(100, 300)
    
                                     
    bonus_text = ""
    if ability == "Scavenger" and random.random() < 0.2:
        shards *= 2
        bonus_text += "\n**Double Shards!** (Scavenger)"
        
    await user_collection.update_one({"id": user_id}, {"$inc": {"balance": shards}}, upsert=True)
    
              
    xp_gain = random.randint(10, 20)
    if ability == "Beginner's Luck":
        xp_gain = int(xp_gain * 1.05)
    await add_pet_xp(user_id, pet["name"], xp_gain)

                                      
    await check_achievements(user_id)

                    
    base_drop_chance = 15 * (1 + luck)                     
    
                                       
    extra_drop = False
    if ability == "Hoarder" and random.random() < 0.05:
        extra_drop = True
    
    if random.uniform(0, 100) <= base_drop_chance or extra_drop:
        tier_key = get_egg_roll(luck)
        tier_data = EGG_TIERS[tier_key]
        
                                
        is_corrupted = random.uniform(0, 100) <= CORRUPTED_EGG_CHANCE
        
        egg_data = {
            "id": f"egg_{random.randint(10000, 99999)}",
            "tier": tier_key, 
            "name": tier_data["name"],
            "obtained_at": datetime.now(),
            "status": "fresh",                               
            "is_corrupted": is_corrupted
        }
        
        await user_collection.update_one({"id": user_id}, {"$push": {"eggs": egg_data}}, upsert=True)
        if extra_drop:
                                        
            extra_egg = egg_data.copy()
            extra_egg["id"] = f"egg_{random.randint(10000, 99999)}"
            extra_egg["tier"] = "common"
            extra_egg["name"] = "🥚 Bonus Common Egg"
            await user_collection.update_one({"id": user_id}, {"$push": {"eggs": extra_egg}}, upsert=True)
            bonus_text += "\n🥚 **Bonus Egg Found!** (Hoarder)"
        
                          
        await update_quest_progress(user_id, "egg_hunter", 1)

        await msg.edit_text(
            f"🎁 **Loot Found!**\n\n"
            f"🥚 **{md_escape(tier_data['name'])}** discovered!\n"
            f"**+{shards} Shards** ⬪{bonus_text}\n"
            f"🆙 **+{xp_gain} XP** for {md_escape(pet['name'])}",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await msg.edit_text(
            f"🌲 **Hunt Complete!**\n\n"
            f"**+{shards} Shards** ⬪{bonus_text}\n"
            f"🆙 **+{xp_gain} XP** for {md_escape(pet['name'])}\n"
            f"_No eggs found this time._",
            parse_mode=ParseMode.MARKDOWN_V2
        )

@app.on_message(filters.command("eggs"))
async def eggs_cmd(_, message: types.Message):
    await show_egg_page(message, 0, message.from_user.id)

async def show_egg_page(message_or_query, page: int, user_id: int):
                                                         
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if not eggs:
        text = "❌ **No eggs found!**\n\nUse `/hunt` to find eggs."
        if isinstance(message_or_query, types.CallbackQuery):
            try:
                await message_or_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
            except:
                pass
        else:
            await message_or_query.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    
                
    page = page % len(eggs)
    egg = eggs[page]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    status = egg.get("status", "fresh")
    
                             
    action_button = None
    status_display = ""
    
    if status == "fresh":
        status_display = f"🛑 **Status:** Not incubated\n⏱️ **Required:** {tier_info['wait_min']} minutes"
        action_button = types.InlineKeyboardButton("🌡️ Start Incubation", callback_data=f"egg_incubate:{page}")                             
    elif status == "incubating":
        hatch_time = egg.get("hatch_time")
        if hatch_time and datetime.now() < hatch_time:
            remaining = hatch_time - datetime.now()
            mins_left = int(remaining.total_seconds() / 60)
            status_display = f"⏳ **Status:** Incubating\n⏱️ **Time Left:** {mins_left} minutes"
            action_button = types.InlineKeyboardButton("⏳ Incubating...", callback_data="egg_wait")
        else:
            status_display = "✅ **Status:** Ready to hatch!"
            action_button = types.InlineKeyboardButton("🎁 Hatch Now!", callback_data=f"egg_hatch:{page}")
    
    text = (
        f"🥚 **Egg Inventory**\n\n"
        f"**{egg.get('name', 'Unknown Egg')}**\n"
        f"{status_display}\n\n"
        f"_Egg {page + 1} of {len(eggs)}_"
    )
    
                   
    buttons = []
    
                    
    nav_row = []
    if len(eggs) > 1:
        nav_row.append(types.InlineKeyboardButton("⬅️", callback_data=f"egg_page:{page - 1}:{user_id}"))
        nav_row.append(types.InlineKeyboardButton(f"{page + 1}/{len(eggs)}", callback_data="egg_noop"))
        nav_row.append(types.InlineKeyboardButton("➡️", callback_data=f"egg_page:{page + 1}:{user_id}"))
        buttons.append(nav_row)
    
                   
    if action_button:
                                                 
        if "egg_incubate" in action_button.callback_data:
             action_button.callback_data = f"egg_incubate:{page}:{user_id}"
        elif "egg_hatch" in action_button.callback_data:
             action_button = types.InlineKeyboardButton("🎁 Hatch Now!", callback_data=f"egg_hatch:{page}:{user_id}")
        buttons.append([action_button])
    
    buttons.append([types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")])
    
    markup = types.InlineKeyboardMarkup(buttons) if buttons else None
    
    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=markup)
        else:
            await message_or_query.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=markup)
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Egg page error: {e}")

                   
@app.on_callback_query(filters.regex(r"^egg_page:"))
async def egg_page_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    page = int(data[1])
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your inventory!", show_alert=True)
        
    await show_egg_page(query, page, owner_id)
    await query.answer()

@app.on_callback_query(filters.regex(r"^egg_incubate:"))
async def egg_incubate_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    page = int(data[1])
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your egg!", show_alert=True)
        
    user_id = owner_id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if page >= len(eggs):
        return await query.answer("❌ Egg not found!", show_alert=True)
    
    egg = eggs[page]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    
                                          
    pets = user.get("pets", [DEFAULT_PET])
    active_pet = next((p for p in pets if p["name"] == user.get("current_pet")), {})
    
    wait_min = tier_info["wait_min"]
    if active_pet.get("ability") == "Caregiver":
        wait_min = int(wait_min * 0.5)
    
                      
    ready_time = datetime.now() + timedelta(minutes=wait_min)
    
    # Use ID-based update to be safe from positional shifts
    await user_collection.update_one(
        {"id": user_id, "eggs.id": egg["id"]},
        {
            "$set": {
                "eggs.$.status": "incubating",
                "eggs.$.hatch_time": ready_time
            }
        }
    )
    
    await query.answer(f"🌡️ Incubation started! Come back in {wait_min} minutes.", show_alert=True)
    await show_egg_page(query, page, user_id)

@app.on_callback_query(filters.regex(r"^egg_hatch:"))
async def egg_hatch_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    page = int(data[1])
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your egg!", show_alert=True)
        
    user_id = owner_id
    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])
    
    if page >= len(eggs):
        return await query.answer("❌ Egg not found!", show_alert=True)
    
    egg = eggs[page]
    
                       
    if egg.get("status") != "incubating":
        return await query.answer("❌ Egg is not incubating!", show_alert=True)
    
    ready_time = egg.get("hatch_time")
    if ready_time and datetime.now() < ready_time:
        remaining = int((ready_time - datetime.now()).total_seconds() / 60)
        return await query.answer(f"⏳ Still incubating! {remaining}m left.", show_alert=True)
    
                   
    await crack_open_egg_inline(query, user_id, egg)

@app.on_callback_query(filters.regex(r"^egg_(wait|noop)$"))
async def egg_noop_callback(_, query: types.CallbackQuery):
    await query.answer()

async def crack_open_egg_inline(query: types.CallbackQuery, user_id: int, egg: dict):
                                          
                               
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})
    
    await query.message.edit_text("🥚 **Cracking open...**", parse_mode=ParseMode.MARKDOWN_V2)
    await asyncio.sleep(2)
    
                     
    if egg.get("is_corrupted", False):
        if random.random() < 0.5:
            await query.message.edit_text("💥 **The egg exploded!**\nIt was corrupted...", parse_mode=ParseMode.MARKDOWN_V2)
            return
        else:
            rarity = RARITY_MAP[9]          
    else:
        rarity_pool = EGG_TIERS[egg["tier"]]["pool"]
        rarity = random.choice(rarity_pool)
    
                     
    waifus = await collection.find({"rarity": rarity}).to_list(length=None)
    if waifus:
        character = random.choice(waifus)
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
        
                  
        await add_xp(user_id, 15, "egg_hatch")
        
        await query.message.edit_text("🎉 **Success! Sending details...**", parse_mode=ParseMode.MARKDOWN_V2)
        await query.message.reply_photo(
            photo=character["img_url"],
            caption=(
                f"🐣 **Hatched Successfully!**\n\n"
                f"📛 **{md_escape(character['name'])}**\n"
                f"✨ **{md_escape(rarity)}**\n"
                f"🎬 {md_escape(character['anime'])}"
            ),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.message.edit_text("⚠️ The egg was empty (DB error).", parse_mode=ParseMode.MARKDOWN_V2)

                                                                            

@app.on_message(filters.command("hatch"))
async def hatch_cmd(_, message: types.Message):
                                    
    await show_egg_page(message, 0, message.from_user.id)

async def crack_open_egg(message, user_id, egg, index):
                 
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})
    
    msg = await message.reply_text("🥚 **Cracking open...**", parse_mode=ParseMode.MARKDOWN_V2)
    await asyncio.sleep(2)
    
                     
    if egg.get("is_corrupted", False):
        if random.random() < 0.5:
            await msg.edit_text("💥 **The egg exploded!**\nIt was corrupted... You got nothing.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        else:
                     
            rarity = RARITY_MAP[9]          
    else:
                       
        rarity_pool = EGG_TIERS[egg["tier"]]["pool"]
        rarity = random.choice(rarity_pool)

                     
    waifus = await collection.find({"rarity": rarity}).to_list(length=None)
    if waifus:
        character = random.choice(waifus)
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
        
                               
        await add_xp(user_id, 15, "egg_hatch")
        
        await msg.edit_text("🎉 Success! Sending details...", parse_mode=ParseMode.MARKDOWN_V2)
        await message.reply_photo(
            photo=character["img_url"],
            caption=f"🐣 **Hatched Successfully!**\n\n"
                    f"📛 **{md_escape(character['name'])}**\n"
                    f"✨ **{md_escape(rarity)}**\n"
                    f"🎬 {md_escape(character['anime'])}",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await msg.edit_text("⚠️ The egg was empty (Database error: No chars for this rarity).", parse_mode=enums.ParseMode.MARKDOWN)
