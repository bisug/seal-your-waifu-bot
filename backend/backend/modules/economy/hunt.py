import asyncio
import logging
import random
import time
import uuid
from datetime import timedelta, timezone

from pyrogram import enums, filters, types
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from backend.core.cache import is_on_cooldown as redis_cooldown
from backend.core.constants import CORRUPTED_EGG_CHANCE, EGG_TIERS
from backend.core.eggs import (
    get_egg_tier_info,
    get_incubating_count,
    get_incubation_wait_minutes,
    normalize_egg_tier,
    roll_egg_tier,
)
from backend.core.keyboard import get_webapp_button
from backend.core.leaderboard import sync_user_to_redis
from backend.core.pass_config import (
    PASS_BENEFITS,
    apply_pass_incubation_bonus,
    get_active_pass_type,
    get_pass_incubation_slots,
)
from backend.core.pets import (
    DEFAULT_PET,
    ensure_user_pet_state,
    find_pet,
    get_effective_affection,
    get_pet_key,
    normalize_pet,
)
from backend.core.progression import add_xp
from backend.core.tasks import run_background_task
from backend.core.user import add_pet_xp, add_user_set_on_insert, get_user_filter
from backend.core.utils import format_currency, get_now_utc, html_escape, reply_media_dynamic
from backend.database import user_collection
from backend.modules.progression.achievements import check_achievements
from backend.modules.progression.quests import update_quest_progress

# Configuration
LOGGER = logging.getLogger(__name__)
def load_handlers(bot):
    """Explicitly register handlers to the bot instance. Resolves multi-bot ghosting."""
    if bot.name != "MainBot":
        return
    bot.add_handler(MessageHandler(hunt_cmd, filters.command("hunt")), group=0)
    bot.add_handler(MessageHandler(eggs_cmd, filters.command(["eggs", "hatch"])), group=0)
    bot.add_handler(CallbackQueryHandler(egg_page_callback, filters.regex(r"^egg_page:(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_incubate_callback, filters.regex(r"^egg_incubate:([^:]+):(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_hatch_callback, filters.regex(r"^egg_hatch:([^:]+):(\d+):(\d+)$")), group=0)
    bot.add_handler(CallbackQueryHandler(egg_noop_callback, filters.regex(r"^egg_noop$")), group=0)
    LOGGER.info(f"Registered Hunt & Egg handlers for {bot.name}")
async def hunt_cmd(bot, message: types.Message):
    """Refactored Hunt Command: High durability, atomic updates."""
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return
    LOGGER.info(f"HUNT_START: User {user_id} via {bot.name}")
    try:
        user = await asyncio.wait_for(user_collection.find_one(get_user_filter(user_id)), timeout=5.0) or {}
        user = await ensure_user_pet_state(user_id, user)
        pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
        current_pet_name = user.get("current_pet", DEFAULT_PET["petid"])
        pet = find_pet(pets, current_pet_name) or DEFAULT_PET
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
        try:
            on_cd, seconds_left = await asyncio.wait_for(redis_cooldown("hunt", user_id, cooldown_duration), timeout=2.5)
            if on_cd:
                return await message.reply_text(f"Please wait <b>{seconds_left}s</b> before hunting again.", parse_mode=enums.ParseMode.HTML)
        except asyncio.TimeoutError:
            LOGGER.warning(f"Cooldown check timed out for {user_id}. Proceeding as fail-safe.")
        msg = await message.reply_text(f"<b>{html_escape(pet['name'])}</b> is going hunting...", parse_mode=enums.ParseMode.HTML)
        await asyncio.sleep(2)
        shards = random.randint(100, 300)
        bonus_text = ""
        pass_type = get_active_pass_type(user)
        pass_benefits = PASS_BENEFITS[pass_type]
        hunt_multiplier = pass_benefits["hunt_multiplier"]
        if pass_type == "elite":
            shards = int(shards * hunt_multiplier)
            bonus_text += "\n<b>+75% Elite Shards!</b>"
        elif pass_type == "premium":
            shards = int(shards * hunt_multiplier)
            bonus_text += "\n<b>+35% Premium Shards!</b>"
        scavenger_chance = 0.2 * aff_multiplier
        if ability == "Scavenger" and random.random() < scavenger_chance:
            shards *= 2
            bonus_text += "\n<b>Double Shards!</b> (Scavenger)"
        xp_gain = random.randint(10, 20)
        luck_modifier = 1.0 + (0.05 * aff_multiplier)
        if ability == "Beginner's Luck":
            xp_gain = int(xp_gain * luck_modifier)
        eggs_to_push = []
        base_drop_chance = min(80, 15 * (1 + luck) * pass_benefits["egg_drop_multiplier"])
        hoarder_chance = 0.05 * aff_multiplier
        pass_bonus_drop = random.random() < pass_benefits.get("bonus_egg_chance", 0)
        hoarder_drop = ability == "Hoarder" and random.random() < hoarder_chance
        extra_drop = hoarder_drop or pass_bonus_drop
        if random.uniform(0, 100) <= base_drop_chance or extra_drop:
            tier_key = roll_egg_tier(luck, pass_benefits["egg_quality_bonus"])
            tier_data = EGG_TIERS.get(tier_key, EGG_TIERS["common"])
            corruption_chance = CORRUPTED_EGG_CHANCE * (1 - pass_benefits.get("corruption_resistance", 0))
            egg_data = {
                "id": f"egg_{int(time.time() * 1000)}_{random.randint(100, 999)}",
                "tier": tier_key,
                "name": tier_data["name"],
                "obtained_at": get_now_utc(),
                "status": "fresh",
                "is_corrupted": random.uniform(0, 100) <= corruption_chance
            }
            eggs_to_push.append(egg_data)
            if extra_drop:
                bonus_tier = roll_egg_tier(luck * 0.5, pass_benefits["egg_quality_bonus"] * 0.5)
                bonus_tier_data = EGG_TIERS.get(bonus_tier, EGG_TIERS["common"])
                extra_egg = egg_data.copy()
                extra_egg.update({
                    "id": f"egg_bonus_{int(time.time() * 1000)}",
                    "tier": bonus_tier,
                    "name": bonus_tier_data["name"],
                    "is_corrupted": random.uniform(0, 100) <= corruption_chance
                })
                eggs_to_push.append(extra_egg)
                bonus_source = "Hoarder" if hoarder_drop else pass_type.capitalize()
                bonus_text += f"\n<b>Bonus Egg Found!</b> ({bonus_source})"
            if pass_type != "free":
                bonus_text += f"\n<b>{pass_type.capitalize()} Egg Luck:</b> improved drop and tier roll"
        update_op = {"$inc": {"balance": shards}}
        if eggs_to_push:
            update_op["$push"] = {"eggs": {"$each": eggs_to_push}}
        await asyncio.wait_for(user_collection.update_one(
            get_user_filter(user_id),
            add_user_set_on_insert(update_op, user_id),
            upsert=True
        ), timeout=5.0)
        run_background_task(add_pet_xp(user_id, get_pet_key(pet), xp_gain))
        if eggs_to_push:
            run_background_task(update_quest_progress(user_id, "egg_hunter", len(eggs_to_push)))
        run_background_task(sync_user_to_redis(user_id))
        run_background_task(check_achievements(user_id))
        found_egg_desc = f"<b>{html_escape(eggs_to_push[0]['name'])}</b> discovered!" if eggs_to_push else ""
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
    tier_key, tier_info = get_egg_tier_info(raw_tier)
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

    # Guard the positional write: if the eggs array shifted between the read
    # and this write (a concurrent hatch $pull), eggs.{page} now points at a
    # different egg. Only upgrade an entry that still has no id, so we never
    # clobber a real egg's state.
    await user_collection.update_one(
        {**get_user_filter(user_id), f"eggs.{page}.id": {"$exists": False}},
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
    raw_tier = egg.get("tier", "common")
    tier_key, tier_info = get_egg_tier_info(raw_tier)
    status = egg.get("status", "fresh")
    action_button = None
    status_display = ""
    if status == "fresh":
        pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
        active_pet = find_pet(pets, user.get("current_pet"))
        base_wait_min = get_incubation_wait_minutes(tier_key, active_pet)
        wait_min = apply_pass_incubation_bonus(base_wait_min, user)
        active_incubations = get_incubating_count(eggs)
        slots = get_pass_incubation_slots(user)
        status_display = (
            f"<b>Status:</b> Not incubated\n"
            f"<b>Required:</b> {wait_min} minutes\n"
            f"<b>Incubators:</b> {active_incubations}/{slots}"
        )
        action_button = types.InlineKeyboardButton("Start Incubation", callback_data=f"egg_incubate:{egg['id']}:{user_id}:{page}")
    elif status == "incubating":
        hatch_time = egg.get("hatch_time")
        if hatch_time:
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
    active_incubations = get_incubating_count(eggs)
    slots = get_pass_incubation_slots(user)
    if active_incubations >= slots:
        return await query.answer(f"All incubators are busy ({active_incubations}/{slots}).", show_alert=True)
    pets = [normalize_pet(p) for p in user.get("pets", [DEFAULT_PET])]
    active_pet = find_pet(pets, user.get("current_pet")) or {}
    raw_tier = egg.get("tier", "common") if isinstance(egg, dict) else egg
    tier_key = normalize_egg_tier(raw_tier)
    base_wait_min = get_incubation_wait_minutes(tier_key, active_pet)
    wait_min = apply_pass_incubation_bonus(base_wait_min, user)
    ready_time = get_now_utc() + timedelta(minutes=wait_min)
    incubate_filter = get_user_filter(owner_id)
    incubate_filter["eggs"] = {"$elemMatch": {"id": egg_id, "status": "fresh"}}
    # Atomic slot guard: the pre-check above reads a stale snapshot, so two
    # concurrent incubations could both pass it. Re-check inside the filter —
    # only proceed while the incubating count is still below the slot limit.
    incubate_filter["$expr"] = {
        "$lt": [
            {"$size": {"$filter": {
                "input": {"$ifNull": ["$eggs", []]},
                "as": "e",
                "cond": {"$eq": ["$$e.status", "incubating"]},
            }}},
            slots,
        ]
    }
    result = await user_collection.update_one(
        incubate_filter,
        {"$set": {
            "eggs.$.status": "incubating",
            "eggs.$.hatch_time": ready_time,
            "eggs.$.incubation_started_at": get_now_utc(),
            "eggs.$.incubation_base_minutes": base_wait_min,
            "eggs.$.incubation_minutes": wait_min,
            "eggs.$.incubation_pass_type": get_active_pass_type(user)
        }}
    )
    if result.modified_count == 0:
        return await query.answer("This egg was already handled.", show_alert=True)
    await query.answer(f"Incubation started! Ready in {wait_min}m.", show_alert=True)
    await show_egg_page(query, page, owner_id)
async def egg_hatch_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    egg_id, owner_id = data[1], int(data[2])
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
        user = await user_collection.find_one(get_user_filter(user_id)) or {}
        pass_type = get_active_pass_type(user)
        pass_benefits = PASS_BENEFITS[pass_type]
        corruption_explosion_chance = 0.3 * (1 - pass_benefits.get("corruption_resistance", 0))
        if egg.get("is_corrupted", False) and random.random() < corruption_explosion_chance:
            await user_collection.update_one(get_user_filter(user_id), {"$pull": {"eggs": {"id": egg["id"]}}})
            return False, "💥 <b>The egg exploded!</b>\nIt was corrupted..."
        tier_key, tier_info = get_egg_tier_info(egg.get("tier", "common"))
        from backend.core.waifu import get_or_load_characters
        chars = []
        for rarity in random.sample(tier_info["pool"], k=len(tier_info["pool"])):
            chars = await get_or_load_characters(rarity)
            if chars:
                break
        if not chars:
            return False, "Egg was empty! No matching characters are available right now."
        character = random.choice(chars)
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
        hatch_xp = 15 + (int(tier_info.get("rank", 0)) * 5)
        await add_xp(user_id, hatch_xp, "egg_hatch")
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
