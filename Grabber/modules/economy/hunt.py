import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from pyrogram import enums, errors, filters, types
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from Grabber import WEB_APP_URL, collection, user_collection
from Grabber.core.cache import invalidate_user_cache
from Grabber.core.cache import is_on_cooldown as redis_cooldown
from Grabber.core.cache import sync_user_to_redis
from Grabber.core.constants import CORRUPTED_EGG_CHANCE, EGG_TIERS
from Grabber.core.keyboard import get_webapp_button
from Grabber.core.progression import add_xp
from Grabber.core.tasks import run_background_task
from Grabber.core.user import add_pet_xp, add_user_set_on_insert, get_user_filter, get_user_id
from Grabber.core.utils import get_now_utc, html_escape, reply_media_dynamic
from Grabber.modules.collection.rarities import RARITY_MAP
from Grabber.modules.progression.achievements import check_achievements
from Grabber.modules.progression.pet import (DEFAULT_PET,
                                             get_effective_affection)
from Grabber.modules.progression.quests import update_quest_progress
# Configuration
LOGGER = logging.getLogger(__name__)
TIER_MAP = {"1": "common", "2": "gold", "3": "void", "4": "gold", "5": "void"}
def load_handlers(bot):
    """Explicitly register handlers to the bot instance. Resolves multi-bot ghosting."""
    if bot.name != "MainBot":
        return
    # Hunt command
    bot.add_handler(MessageHandler(hunt_cmd, filters.command("hunt")), group=0)
    # Eggs/Inventory command
    bot.add_handler(MessageHandler(eggs_cmd, filters.command(["eggs", "hatch"])), group=0)
    # Callbacks
    bot.add_handler(CallbackQueryHandler(egg_page_callback, filters.regex(r"^egg_page:(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_incubate_callback, filters.regex(r"^egg_incubate:([^:]+):(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_hatch_callback, filters.regex(r"^egg_hatch:([^:]+):(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_noop_callback, filters.regex(r"^egg_noop$")), group=0)
    LOGGER.info(f"Registered Hunt & Egg handlers for {bot.name}")
def get_egg_roll(luck_multiplier):
    """Determine the tier of the egg found based on luck."""
    roll = random.uniform(0, 100)
    void_c = EGG_TIERS["void"]["chance"] * (1 + luck_multiplier)
    gold_c = EGG_TIERS["gold"]["chance"] * (1 + luck_multiplier)
    if roll <= void_c: return "void"
    if roll <= (void_c + gold_c): return "gold"
    return "common"
async def hunt_cmd(bot, message: types.Message):
    """Refactored Hunt Command: High durability, atomic updates."""
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return
    LOGGER.info(f"HUNT_START: User {user_id} via {bot.name}")
    try:
        # 1. Fetch User and Active Pet
        user = await asyncio.wait_for(user_collection.find_one(get_user_filter(user_id)), timeout=5.0) or {}
        pets = user.get("pets", [DEFAULT_PET])
        current_pet_name = user.get("current_pet", DEFAULT_PET["name"])
        pet = next((p for p in pets if p.get("name") == current_pet_name), DEFAULT_PET)
        affection = get_effective_affection(pet)
        aff_multiplier = 1.0
        if affection >= 80:
            aff_multiplier = 1.2
        elif affection <= 20:
            aff_multiplier = 0.8
        ability = pet.get("ability", "None")
        luck = pet.get("luck", 0.1) * aff_multiplier
        base_cd = 50 if ability == "Speedster" else 60
        cooldown_duration = int(base_cd / aff_multiplier)
        # 2. Cooldown Check (Safe Fail-Open)
        try:
            on_cd, seconds_left = await asyncio.wait_for(redis_cooldown("hunt", user_id, cooldown_duration), timeout=2.5)
            if on_cd:
                return await message.reply_text(f"Please wait <b>{seconds_left}s</b> before hunting again.", parse_mode=enums.ParseMode.HTML)
        except asyncio.TimeoutError:
            LOGGER.warning(f"Cooldown check timed out for {user_id}. Proceeding as fail-safe.")
        # 3. Execution Phase
        msg = await message.reply_text(f"<b>{html_escape(pet['name'])}</b> is going hunting...", parse_mode=enums.ParseMode.HTML)
        await asyncio.sleep(2)
        # Calculate Shards
        shards = random.randint(100, 300)
        bonus_text = ""
        pass_type = user.get("pass_type", "free")
        if pass_type == "elite":
            shards = int(shards * 1.5)
            bonus_text += "\n<b>+50% Elite Bonus!</b>"
        elif pass_type == "premium":
            shards = int(shards * 1.2)
            bonus_text += "\n<b>+20% Premium Bonus!</b>"
        scavenger_chance = 0.2 * aff_multiplier
        if ability == "Scavenger" and random.random() < scavenger_chance:
            shards *= 2
            bonus_text += "\n<b>Double Shards!</b> (Scavenger)"
        # Calculate XP
        xp_gain = random.randint(10, 20)
        luck_modifier = 1.0 + (0.05 * aff_multiplier)
        if ability == "Beginner's Luck":
            xp_gain = int(xp_gain * luck_modifier)
        # 4. Loot Determination
        eggs_to_push = []
        base_drop_chance = 15 * (1 + luck)
        hoarder_chance = 0.05 * aff_multiplier
        extra_drop = (ability == "Hoarder" and random.random() < hoarder_chance)
        if random.uniform(0, 100) <= base_drop_chance or extra_drop:
            tier_key = get_egg_roll(luck)
            tier_data = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
            egg_data = {
                "id": f"egg_{int(time.time() * 1000)}_{random.randint(100, 999)}",
                "tier": tier_key,
                "name": tier_data["name"],
                "obtained_at": get_now_utc(),
                "status": "fresh",
                "is_corrupted": random.uniform(0, 100) <= CORRUPTED_EGG_CHANCE
            }
            eggs_to_push.append(egg_data)
            if extra_drop:
                extra_egg = egg_data.copy()
                extra_egg.update({
                    "id": f"egg_bonus_{int(time.time() * 1000)}",
                    "tier": "common",
                    "name": "🥚 Bonus Common Egg"
                })
                eggs_to_push.append(extra_egg)
                bonus_text += "\n<b>Bonus Egg Found!</b> (Hoarder)"
        # 5. Atomic Update
        update_op = {"$inc": {"balance": shards}}
        if eggs_to_push:
            update_op["$push"] = {"eggs": {"$each": eggs_to_push}}
        await asyncio.wait_for(user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert(update_op, user_id),
            upsert=True
        ), timeout=5.0)
        # 6. Side Effects
        run_background_task(add_pet_xp(user_id, pet["name"], xp_gain))
        if eggs_to_push:
            run_background_task(update_quest_progress(user_id, "egg_hunter", len(eggs_to_push)))
        run_background_task(sync_user_to_redis(user_id))
        run_background_task(check_achievements(user_id))
        # 7. Final Response
        found_egg_desc = f"<b>{html_escape(eggs_to_push[0]['name'])}</b> discovered!" if eggs_to_push else ""
        from Grabber.core.utils import format_currency
        shards_text = format_currency(shards)
        final_text = (
            f"<b>Hunt Complete, Collector!</b>\n\n"
            f"{'<b>Egg Found!</b>' if eggs_to_push else '<i>No eggs found this time.</i>'}\n"
            f"{found_egg_desc}\n"
            f"<b>+{shards_text}</b>{bonus_text}\n"
            f"<b>+{xp_gain} XP</b> for {html_escape(pet['name'])}"
        )
        await msg.edit_text(final_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.exception("HUNT_CRASH")
        await message.reply_text(f"<b>Hunt Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)
async def eggs_cmd(bot, message: types.Message):
    """View egg inventory."""
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return
    await show_egg_page(message, 0, user_id)


async def _ensure_egg_document(user_id: int, eggs: list, page: int) -> dict:
    """Normalize legacy egg entries so callbacks can target a stable egg id."""
    raw_egg = eggs[page]
    if isinstance(raw_egg, dict) and raw_egg.get("id"):
        return raw_egg

    raw_tier = raw_egg.get("tier", "common") if isinstance(raw_egg, dict) else raw_egg
    tier_key = TIER_MAP.get(str(raw_tier), str(raw_tier))
    tier_info = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
    egg = {
        "id": f"egg_{uuid.uuid4().hex[:12]}",
        "tier": tier_key,
        "name": tier_info["name"],
        "status": raw_egg.get("status", "fresh") if isinstance(raw_egg, dict) else "fresh",
        "is_corrupted": raw_egg.get("is_corrupted", False) if isinstance(raw_egg, dict) else False,
    }
    hatch_time = raw_egg.get("hatch_time") if isinstance(raw_egg, dict) else None
    if hatch_time:
        egg["hatch_time"] = hatch_time

    await user_collection.update_one(
        get_user_filter(user_id),
        {"$set": {f"eggs.{page}": egg}}
    )
    return egg


async def show_egg_page(message_or_query, page: int, user_id: int):
    """Render egg inventory page."""
    user = await user_collection.find_one(get_user_filter(user_id)) or {}
    eggs = user.get("eggs", [])
    if not eggs:
        text = "<b>No eggs found!</b>\n\nUse <code>/hunt</code> to find eggs."
        if isinstance(message_or_query, types.CallbackQuery):
            return await message_or_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML)
        return await message_or_query.reply_text(text, parse_mode=enums.ParseMode.HTML)
    page = page % len(eggs)
    egg = await _ensure_egg_document(user_id, eggs, page)
    # Handle legacy/numeric tiers
    raw_tier = egg.get("tier", "common")
    tier_key = TIER_MAP.get(str(raw_tier), str(raw_tier))
    tier_info = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
    status = egg.get("status", "fresh")
    action_button = None
    status_display = ""
    if status == "fresh":
        status_display = f"<b>Status:</b> Not incubated\n<b>Required:</b> {tier_info['wait_min']} minutes"
        action_button = types.InlineKeyboardButton("Start Incubation", callback_data=f"egg_incubate:{egg['id']}:{user_id}:{page}")
    elif status == "incubating":
        hatch_time = egg.get("hatch_time")
        if hatch_time:
            # Ensure hatch_time is aware
            if hatch_time.tzinfo is None:
                hatch_time = hatch_time.replace(tzinfo=timezone.utc)
            now = get_now_utc()
            if now < hatch_time:
                remaining = hatch_time - now
                mins_left = int(remaining.total_seconds() / 60)
                status_display = f"<b>Status:</b> Incubating\n<b>Time Left:</b> {mins_left} minutes"
                action_button = types.InlineKeyboardButton("Incubating...", callback_data="egg_noop")
            else:
                status_display = "<b>Status:</b> Ready to hatch!"
                action_button = types.InlineKeyboardButton("Hatch Egg", callback_data=f"egg_hatch:{egg['id']}:{user_id}:{page}")
    text = (
        f"<b>Collector Stash</b>\n\n"
        f"<b>{html_escape(egg.get('name', tier_info['name']))}</b>\n"
        f"{status_display}\n\n"
        f"<i>Egg {page + 1} of {len(eggs)}</i>"
    )
    buttons = []
    if len(eggs) > 1:
        buttons.append([
            types.InlineKeyboardButton("Prev", callback_data=f"egg_page:{page - 1}:{user_id}"),
            types.InlineKeyboardButton(f"{page + 1}/{len(eggs)}", callback_data="egg_noop"),
            types.InlineKeyboardButton("Next", callback_data=f"egg_page:{page + 1}:{user_id}")
        ])
    if action_button:
        buttons.append([action_button])
    if isinstance(message_or_query, types.CallbackQuery):
        is_private = message_or_query.message.chat.type == enums.ChatType.PRIVATE
    else:
        is_private = message_or_query.chat.type == enums.ChatType.PRIVATE
    webapp_btn = get_webapp_button(is_private, path="#incubation")
    if webapp_btn:
        buttons.append([webapp_btn])
    buttons.append([types.InlineKeyboardButton("Back to Hub", callback_data="hub_main")])
    markup = types.InlineKeyboardMarkup(buttons)
    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
        else:
            await message_or_query.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=markup)
    except Exception as e:
        LOGGER.debug(f"Egg UI error: {e}")
async def egg_page_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    page, owner_id = int(data[1]), int(data[2])
    if query.from_user.id != owner_id:
        return await query.answer("Not your inventory!", show_alert=True)
    await query.answer()
    await show_egg_page(query, page, owner_id)
async def egg_incubate_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    egg_id, owner_id = data[1], int(data[2])
    page = int(data[3])
    if query.from_user.id != owner_id:
        return await query.answer("Not your egg!", show_alert=True)
    user = await user_collection.find_one(get_user_filter(owner_id)) or {}
    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if isinstance(e, dict) and e.get("id") == egg_id), None)
    if not egg:
        return await query.answer("Egg not found!")
    if egg.get("status", "fresh") != "fresh":
        return await query.answer("This egg is already incubating or hatched.", show_alert=True)
    # Calculate incubation time
    pets = user.get("pets", [DEFAULT_PET])
    active_pet = next((p for p in pets if p.get("name") == user.get("current_pet")), {})
    raw_tier = egg.get("tier", "common") if isinstance(egg, dict) else egg
    tier_key = TIER_MAP.get(str(raw_tier), str(raw_tier))
    tier_info = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
    wait_min = tier_info["wait_min"]
    if active_pet.get("ability") == "Caregiver":
        affection = get_effective_affection(active_pet)
        aff_multiplier = 1.0
        if affection >= 80:
            aff_multiplier = 1.2
        elif affection <= 20:
            aff_multiplier = 0.8
        wait_min = int(wait_min * (0.5 / aff_multiplier))
    ready_time = get_now_utc() + timedelta(minutes=wait_min)
    incubate_filter = get_user_filter(owner_id)
    incubate_filter["eggs"] = {"$elemMatch": {"id": egg_id, "status": "fresh"}}
    result = await user_collection.update_one(
        incubate_filter,
        {"$set": {
            "eggs.$.status": "incubating",
            "eggs.$.hatch_time": ready_time
        }}
    )
    if result.modified_count == 0:
        return await query.answer("This egg was already handled.", show_alert=True)
    await query.answer(f"Incubation started! Ready in {wait_min}m.", show_alert=True)
    await show_egg_page(query, page, owner_id)
async def egg_hatch_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    egg_id, owner_id = data[1], int(data[2])
    page = int(data[3])
    if query.from_user.id != owner_id:
        return await query.answer("Not your egg!", show_alert=True)
    user = await user_collection.find_one(get_user_filter(owner_id)) or {}
    eggs = user.get("eggs", [])
    egg = next((e for e in eggs if isinstance(e, dict) and e.get("id") == egg_id), None)
    if not egg:
        return await query.answer("Egg not found!")
    if egg.get("status") != "incubating":
        return await query.answer("Not ready to hatch!")
    hatch_time = egg.get("hatch_time")
    if hatch_time:
        if hatch_time.tzinfo is None:
            hatch_time = hatch_time.replace(tzinfo=timezone.utc)
        if get_now_utc() < hatch_time:
            return await query.answer("Still incubating!")
    # Restore process_egg_hatch compatibility
    success, result = await process_egg_hatch(owner_id, egg)
    if not success:
        return await query.message.edit_text(result, parse_mode=enums.ParseMode.HTML)
    character = result
    await query.message.edit_text("<b>Success! Sending details...</b>", parse_mode=enums.ParseMode.HTML)
    await reply_media_dynamic(query.message, character["img_url"],
        caption=(
            f"<b>Hatched Successfully!</b>\n\n"
            f"<b>{html_escape(character['name'])}</b>\n"
            f"<b>{html_escape(character['rarity'])}</b>\n"
            f"{html_escape(character['anime'])}"
        ),
        parse_mode=enums.ParseMode.HTML
    )
async def process_egg_hatch(user_id: int, egg: dict) -> tuple[bool, any]:
    """Compatibility function for both bot callbacks and webapp requests."""
    try:
        # Handle corruption explosion
        if egg.get("is_corrupted", False) and random.random() < 0.3:
            await user_collection.update_one(get_user_filter(user_id), {"$pull": {"eggs": {"id": egg["id"]}}})
            return False, "💥 <b>The egg exploded!</b>\nIt was corrupted..."
        # Pick character
        tier_info = EGG_TIERS.get(egg["tier"], EGG_TIERS["common"])
        rarity = random.choice(tier_info["pool"])
        from Grabber.core.waifu import get_or_load_characters
        chars = await get_or_load_characters(rarity)
        if not chars:
            return False, "Egg was empty! (Database Error)"
        character = random.choice(chars)
        # Atomic: Pull Egg, Push Char
        hatch_filter = get_user_filter(user_id)
        hatch_filter["eggs.id"] = egg["id"]
        result = await user_collection.update_one(
            hatch_filter,
            {
                "$pull": {"eggs": {"id": egg["id"]}},
                "$push": {"characters": character},
                "$inc": {"char_count": 1, "hatch_count": 1}
            }
        )
        if result.modified_count == 0:
            return False, "This egg has already hatched!"
        await add_xp(user_id, 15, "egg_hatch")

        # Track Quests and Achievements
        run_background_task(update_quest_progress(user_id, "egg_hatcher", 1))
        run_background_task(update_quest_progress(user_id, "weekly_hatcher", 1))
        run_background_task(update_quest_progress(user_id, "pass_hatcher", 1))
        run_background_task(check_achievements(user_id))

        await sync_user_to_redis(user_id)
        return True, character
    except Exception as e:
        LOGGER.error(f"process_egg_hatch error: {e}")
        return False, f"Error: {str(e)}"
async def egg_noop_callback(_, query: types.CallbackQuery):
    await query.answer()
