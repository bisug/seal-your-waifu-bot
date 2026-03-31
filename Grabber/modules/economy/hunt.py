from Grabber.core.utils import reply_media_dynamic
import asyncio
import random
import time
import uuid
from datetime import datetime, timedelta
from pyrogram import filters, types, enums, errors
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import user_collection, collection, app, WEB_APP_URL
from Grabber.core.user import add_pet_xp
from Grabber.core.progression import add_xp
from Grabber.modules.progression.quests import update_quest_progress
from Grabber.modules.progression.achievements import check_achievements
from Grabber.modules.collection.rarities import RARITY_MAP
from Grabber.core.keyboard import get_webapp_button
from Grabber.core.cache import invalidate_user_cache
from config import config


EGG_TIERS = {
    "common": {"name": "Common Egg", "chance": 70, "pool": [RARITY_MAP[1], RARITY_MAP[2]], "wait_min": 5},
    "gold":   {"name": "Golden Egg", "chance": 25, "pool": [RARITY_MAP[3], RARITY_MAP[4]], "wait_min": 30},
    "void":   {"name": "Void Egg",   "chance": 5,  "pool": [RARITY_MAP[5], RARITY_MAP[6]], "wait_min": 180}
}


CORRUPTED_EGG_CHANCE = 5


from Grabber.modules.progression.pet import DEFAULT_PET

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

    user = await user_collection.find_one({"id": user_id}) or {}
    pets = user.get("pets", [DEFAULT_PET])
    current = user.get("current_pet", DEFAULT_PET["name"])
    pet = next((p for p in pets if p["name"] == current), DEFAULT_PET)

    ability = pet.get("ability", None)
    luck = pet.get("luck", 0.1)

    # Determine ability-aware cooldown duration
    cooldown_duration = 50 if ability == "Speedster" else 60

    # Redis-based cooldown check (survives restarts)
    from Grabber.core.cache import is_on_cooldown as redis_cooldown
    on_cd, seconds_left = await redis_cooldown("hunt", user_id, cooldown_duration)
    if on_cd:
        return await message.reply_text(f"⏳ Please wait {seconds_left}s before hunting again.", parse_mode=ParseMode.HTML)

    msg = await message.reply_text(f"🦊 <b>{html_escape(pet['name'])}</b> is going hunting...", parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    shards = random.randint(100, 300)

    bonus_text = ""
    pass_type = user.get("pass_type", "free")
    if pass_type == "elite":
        shards = int(shards * 1.5)
        bonus_text += "\n💎 <b>+50% Elite Bonus!</b>"
    elif pass_type == "premium":
        shards = int(shards * 1.2)
        bonus_text += "\n💎 <b>+20% Premium Bonus!</b>"

    if ability == "Scavenger" and random.random() < 0.2:
        shards *= 2
        bonus_text += "\n<b>Double Shards!</b> (Scavenger)"

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
            "id": f"egg_{int(time.time() * 1000)}_{random.randint(100, 999)}",
            "tier": tier_key,
            "name": tier_data["name"],
            "obtained_at": datetime.now(),
            "status": "fresh",
            "is_corrupted": is_corrupted
        }

        eggs_to_push = [egg_data]
        if extra_drop:
            extra_egg = egg_data.copy()
            extra_egg["id"] = f"egg_{int(time.time() * 1000)}_{random.randint(100, 999)}_b"
            extra_egg["tier"] = "common"
            extra_egg["name"] = "🥚 Bonus Common Egg"
            eggs_to_push.append(extra_egg)
            bonus_text += "\n🥚 <b>Bonus Egg Found!</b> (Hoarder)"

        # Single atomic write: balance + all eggs at once
        await user_collection.update_one(
            {"id": user_id},
            {
                "$inc": {"balance": shards},
                "$push": {"eggs": {"$each": eggs_to_push}}
            },
            upsert=True
        )
        await invalidate_user_cache(user_id)


        await update_quest_progress(user_id, "egg_hunter", 1)

        await msg.edit_text(
            f"🎁 <b>Loot Found!</b>\n\n"
            f"🥚 <b>{html_escape(tier_data['name'])}</b> discovered!\n"
            f"<b>+{shards} Shards</b> ⬪{bonus_text}\n"
            f"🆙 <b>+{xp_gain} XP</b> for {html_escape(pet['name'])}",
            parse_mode=ParseMode.HTML
        )
    else:
        # No egg — single write for shards only
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": shards}}, upsert=True)
        await invalidate_user_cache(user_id)
        await msg.edit_text(
            f"🌲 <b>Hunt Complete!</b>\n\n"
            f"<b>+{shards} Shards</b> ⬪{bonus_text}\n"
            f"🆙 <b>+{xp_gain} XP</b> for {html_escape(pet['name'])}\n"
            f"<i>No eggs found this time.</i>",
            parse_mode=ParseMode.HTML
        )

@app.on_message(filters.command("eggs"))
async def eggs_cmd(_, message: types.Message):
    await show_egg_page(message, 0, message.from_user.id)

async def show_egg_page(message_or_query, page: int, user_id: int):

    user = await user_collection.find_one({"id": user_id}) or {}
    eggs = user.get("eggs", [])

    if not eggs:
        text = "❌ <b>No eggs found!</b>\n\nUse <code>/hunt</code> to find eggs."
        if isinstance(message_or_query, types.CallbackQuery):
            try:
                await message_or_query.message.edit_text(text, parse_mode=ParseMode.HTML)
            except:
                pass
        else:
            await message_or_query.reply_text(text, parse_mode=ParseMode.HTML)
        return


    page = page % len(eggs)
    egg = eggs[page]
    tier_info = EGG_TIERS.get(egg.get("tier", "common"))
    status = egg.get("status", "fresh")


    action_button = None
    status_display = ""

    if status == "fresh":
        status_display = f"🛑 <b>Status:</b> Not incubated\n⏱️ <b>Required:</b> {tier_info['wait_min']} minutes"
        action_button = types.InlineKeyboardButton("Start Incubation", callback_data=f"egg_incubate:{page}", style=enums.ButtonStyle.SUCCESS)
    elif status == "incubating":
        hatch_time = egg.get("hatch_time")
        if hatch_time and datetime.now() < hatch_time:
            remaining = hatch_time - datetime.now()
            mins_left = int(remaining.total_seconds() / 60)
            status_display = f"⏳ <b>Status:</b> Incubating\n⏱️ <b>Time Left:</b> {mins_left} minutes"
            action_button = types.InlineKeyboardButton("Incubating...", callback_data="egg_wait")
        else:
            status_display = "✅ <b>Status:</b> Ready to hatch!"
            action_button = types.InlineKeyboardButton("Hatch Egg", callback_data=f"egg_hatch:{page}", style=enums.ButtonStyle.SUCCESS)

    text = (
        f"🥚 <b>Egg Inventory</b>\n\n"
        f"<b>{html_escape(egg.get('name', 'Unknown Egg'))}</b>\n"
        f"{status_display}\n\n"
        f"<i>Egg {page + 1} of {len(eggs)}</i>"
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
             action_button = types.InlineKeyboardButton("🎁 Hatch Now!", callback_data=f"egg_hatch:{page}:{user_id}", style=enums.ButtonStyle.SUCCESS)
        buttons.append([action_button])

    is_private = False
    if isinstance(message_or_query, types.CallbackQuery):
        is_private = message_or_query.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query.chat.type == enums.ChatType.PRIVATE
        
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        buttons.append([webapp_btn])

    buttons.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])

    markup = types.InlineKeyboardMarkup(buttons) if buttons else None

    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await message_or_query.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
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

    await query.answer()  # Dismiss spinner instantly
    await show_egg_page(query, page, owner_id)

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
    await query.answer()  # Instant dismiss

async def process_egg_hatch(user_id: int, egg: dict):
    """Core logic for hatching an egg. Returns (success: bool, result: dict_or_error_msg)."""
    if egg.get("is_corrupted", False):
        if random.random() < 0.5:
            # Remove egg only on explosion
            await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})
            return False, "💥 <b>The egg exploded!</b>\nIt was corrupted..."
        rarity = RARITY_MAP[9]
    else:
        rarity_pool = EGG_TIERS[egg["tier"]]["pool"]
        rarity = random.choice(rarity_pool)

    # Remove egg after rarity is determined (successful hatch)
    await user_collection.update_one({"id": user_id}, {"$pull": {"eggs": {"id": egg["id"]}}})

    from Grabber.core.waifu import get_or_load_characters
    waifus = await get_or_load_characters(rarity)
    
    if not waifus:
        return False, "⚠️ The egg was empty (Database error: No chars for this rarity)."

    character = random.choice(waifus)
    await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}}, upsert=True)
    await add_xp(user_id, 15, "egg_hatch")
    
    return True, character


async def crack_open_egg_inline(query: types.CallbackQuery, user_id: int, egg: dict):
    await query.message.edit_text("🥚 <b>Cracking open...</b>", parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    success, result = await process_egg_hatch(user_id, egg)
    
    if not success:
        await query.message.edit_text(result, parse_mode=ParseMode.HTML)
        return

    character = result
    await query.message.edit_text("🎉 <b>Success! Sending details...</b>", parse_mode=ParseMode.HTML)
    await reply_media_dynamic(query.message, character["img_url"],
        caption=(
            f"🐣 <b>Hatched Successfully!</b>\n\n"
            f"📛 <b>{html_escape(character['name'])}</b>\n"
            f"✨ <b>{html_escape(character['rarity'])}</b>\n"
            f"🎬 {html_escape(character['anime'])}"
        ),
        parse_mode=ParseMode.HTML
    )

@app.on_message(filters.command("hatch"))
async def hatch_cmd(_, message: types.Message):
    await show_egg_page(message, 0, message.from_user.id)

async def crack_open_egg(message, user_id, egg, index):
    msg = await message.reply_text("🥚 <b>Cracking open...</b>", parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    success, result = await process_egg_hatch(user_id, egg)
    
    if not success:
        await msg.edit_text(result, parse_mode=ParseMode.HTML)
        return

    character = result
    await msg.edit_text("🎉 Success! Sending details...", parse_mode=ParseMode.HTML)
    await reply_media_dynamic(message, character["img_url"],
        caption=f"🐣 <b>Hatched Successfully!</b>\n\n"
                f"📛 <b>{html_escape(character['name'])}</b>\n"
                f"✨ <b>{html_escape(character['rarity'])}</b>\n"
                f"🎬 {html_escape(character['anime'])}",
        parse_mode=ParseMode.HTML
    )
