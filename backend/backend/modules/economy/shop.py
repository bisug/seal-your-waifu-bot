import random
from datetime import datetime, timezone

from pymongo import ReturnDocument
from pyrogram import enums, errors, filters, types

from backend.client import app
from backend.core.constants import (
    LEVEL_BUY_SHARD_COST,
    RARITY_PRICES,
    RARITY_STOCK_LIMITS,
    SHARDS_PER_ZENITH,
    SHOP_LIMIT,
)
from backend.core.keyboard import KeyboardBuilder, get_webapp_button
from backend.core.leaderboard import sync_user_to_redis
from backend.core.logging import get_logger
from backend.core.sessions import create_session, get_session
from backend.core.user import get_user_filter
from backend.core.utils import handle_errors, html_escape, reply_media_dynamic
from backend.database import collection, daily_shop_collection, user_collection
from backend.database.models import Character, User
from backend.modules.collection.rarities import SHOP_RARITY_WEIGHTS
from backend.modules.progression.achievements import check_achievements
from backend.modules.progression.quests import update_quest_progress
from config import config

LOGGER = get_logger(__name__)

# Characters offered in the daily shop rotation.
DAILY_SHOP_SIZE = 10

async def get_daily_shop_characters():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # 1. Check persistent daily storage
    shop_doc = await daily_shop_collection.find_one({"date": today})
    if shop_doc:
        char_ids = shop_doc.get("character_ids", [])
        chars_raw = await collection.find({"id": {"$in": char_ids}}).to_list(length=len(char_ids))
        char_map = {c["id"]: c for c in chars_raw}
        chars_raw = [char_map[cid] for cid in char_ids if cid in char_map]
        return [Character(**c) for c in chars_raw]

    # 2. If it's a new day, pick DAILY_SHOP_SIZE new characters from various rarities
    rarities = list(SHOP_RARITY_WEIGHTS.keys())
    weights = list(SHOP_RARITY_WEIGHTS.values())

    selected_raw = []
    attempts = 0
    # Try to pick DAILY_SHOP_SIZE unique characters of potentially different rarities
    while len(selected_raw) < DAILY_SHOP_SIZE and attempts < DAILY_SHOP_SIZE * 4:
        attempts += 1
        r = random.choices(rarities, weights=weights, k=1)[0]
        pipeline = [
            {"$match": {"rarity": r, "id": {"$nin": [c["id"] for c in selected_raw]}}},
            {"$sample": {"size": 1}}
        ]
        cursor = await collection.aggregate(pipeline)
        res = await cursor.to_list(length=1)
        if res:
            selected_raw.append(res[0])

    if not selected_raw:
        LOGGER.warning("No characters found for daily shop selection.")
        return []

    selected_ids = [c["id"] for c in selected_raw]
    # 3. Save for the day without deleting another concurrent rotation.
    shop_doc = await daily_shop_collection.find_one_and_update(
        {"date": today},
        {
            "$setOnInsert": {
                "date": today,
                "character_ids": selected_ids,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    await daily_shop_collection.delete_many({"date": {"$ne": today}})
    final_ids = shop_doc.get("character_ids", selected_ids) if shop_doc else selected_ids
    if final_ids == selected_ids:
        return [Character(**c) for c in selected_raw]
    chars_raw = await collection.find({"id": {"$in": final_ids}}).to_list(length=len(final_ids))
    char_map = {c["id"]: c for c in chars_raw}
    return [Character(**char_map[cid]) for cid in final_ids if cid in char_map]
SHOP_BANNER = config.PHOTO_URL[0] if config.PHOTO_URL else None
@app.on_message(filters.command("cshop"))
@handle_errors
async def cshop_cmd(_, message: types.Message):
    chars = await get_daily_shop_characters()
    if not chars:
        await message.reply_text("<b>No shop characters available.</b>", parse_mode=enums.ParseMode.HTML)
        return
    user_id = message.from_user.id
    chars_data = [c.model_dump() for c in chars]
    await create_session(f"shop_{user_id}", {"shop": chars_data, "page": 0})
    await send_shop_message(message, user_id)
@app.on_message(filters.command("shop"))
@handle_errors
async def shop_hub(_, message: types.Message):
    await send_shop_hub(message)
async def send_shop_hub(message_or_query):
    text = (
        "<b>Seal Shop</b>\n\n"
        "Open the Mini App shop, browse today's character rotation, manage pets, or view the Battle Pass."
    )
    is_private = (message_or_query.message if isinstance(message_or_query, types.CallbackQuery) else message_or_query).chat.type == enums.ChatType.PRIVATE
    builder = KeyboardBuilder()
    webapp_btn = get_webapp_button(is_private, path="#shop")
    if webapp_btn:
        builder.add_row(webapp_btn)
    builder.add_row(
        types.InlineKeyboardButton("Character Rotation", callback_data="hub_char"),
        types.InlineKeyboardButton("Battle Pass", callback_data="hub_pass"),
    )
    builder.add_row(
        types.InlineKeyboardButton("Pet Shop", callback_data="hub_pet"),
        types.InlineKeyboardButton("Currency Exchange", callback_data="exchange_help"),
    )
    reply_markup = builder.build()
    try:
        if isinstance(message_or_query, types.CallbackQuery):
            if SHOP_BANNER:
                await message_or_query.edit_message_media(
                    media=types.InputMediaPhoto(media=SHOP_BANNER, caption=text, parse_mode=enums.ParseMode.HTML),
                    reply_markup=reply_markup
                )
            else:
                await message_or_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            if SHOP_BANNER:
                await reply_media_dynamic(message_or_query, SHOP_BANNER, caption=text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML
                )
            else:
                await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error in send_shop_hub: {e}")
        if isinstance(message_or_query, types.CallbackQuery):
            try:
                await message_or_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            except errors.RPCError as e:
                LOGGER.debug(f"Non-critical fallback error: {e}")
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)


@app.on_callback_query(filters.regex(r"^exchange_help$"))
@handle_errors
async def exchange_help_callback(_, query: types.CallbackQuery):
    await query.answer()
    buttons = []
    webapp_btn = get_webapp_button(query.message.chat.type == enums.ChatType.PRIVATE, path="#exchange")
    if webapp_btn:
        buttons.append([webapp_btn])
    await query.message.reply_text(
        "<b>Currency Exchange</b>\n\n"
        f"<b>Rate:</b> {SHARDS_PER_ZENITH:,} Shards = 1 Zenith\n\n"
        f"<code>/exchange {SHARDS_PER_ZENITH}</code> - Shards to Zenith\n"
        "<code>/shard 1</code> - Zenith to Shards",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(buttons) if buttons else None,
    )
@app.on_callback_query(filters.regex(r"^hub_(char|pet|pass|egg|main)$"))
@handle_errors
async def hub_callback_handler(_, query: types.CallbackQuery):
    await query.answer()  # Dismiss spinner instantly
    choice = query.data.split("_")[1]
    if choice == "main":
        await send_shop_hub(query)
    elif choice == "char":
        chars = await get_daily_shop_characters()
        if not chars:
            return await query.answer("No shop characters available.", show_alert=True)
        chars_data = [c.model_dump() for c in chars]
        await create_session(f"shop_{query.from_user.id}", {"shop": chars_data, "page": 0})
        await send_shop_message(query, query.from_user.id)
    elif choice == "pet":
        import backend.modules.progression.pet as pet_module
        await pet_module.send_petshop_page(query, 0, query.from_user.id)
    elif choice == "pass":
        import backend.modules.progression.battlepass as pass_module
        await pass_module.view_pass_inline(query)
@app.on_callback_query(filters.regex(r"^shop_back_(\d+)$"))
@handle_errors
async def shop_back_handler(_, query: types.CallbackQuery):
    owner_id = int(query.data.split("_")[2])
    if query.from_user.id != owner_id:
        return await query.answer("Not yours!", show_alert=True)
    await send_shop_message(query, owner_id)
async def send_shop_message(message, user_id):
    session = await get_session(f"shop_{user_id}")
    if not session:
        return
    page = session.get("page", 0)
    chars_data = session.get("shop", [])
    chars = [Character(**c) for c in chars_data]
    char = chars[page]
    price = RARITY_PRICES.get(char.rarity, 5)
    stock_limit = RARITY_STOCK_LIMITS.get(char.rarity, SHOP_LIMIT)
    user_raw = await user_collection.find_one(get_user_filter(user_id))
    user = User(**user_raw) if user_raw else None
    zenith_balance = user.zenith if user else 0
    sold_count = getattr(char, "sold_count", 0)
    stock_display = f"{sold_count}/{stock_limit}"
    if sold_count >= stock_limit:
        stock_display = "SOLD OUT"
    text = (
        f"<b>Character Shop</b>\n"
        f"⧫ <b>Zenith Balance:</b> <code>{zenith_balance:,}</code>\n\n"
        f"<b>ID:</b> <code>{char.id}</code>\n"
        f"<b>Name:</b> {html_escape(char.name)}\n"
        f"<b>Anime:</b> {html_escape(char.anime)}\n"
        f"<b>Rarity:</b> {html_escape(char.rarity)}\n"
        f"<b>Stock:</b> {stock_display}\n"
        f"<b>Price:</b> <code>{price}</code> ⧫"
    )
    builder = KeyboardBuilder()
    webapp_btn = get_webapp_button(user_id == message.from_user.id if hasattr(message, "from_user") else True, path="#shop")
    if webapp_btn:
        builder.add_row(webapp_btn)
    builder.add_button("Buy Character", callback_data=f"ask_buy_char_{char.id}_{user_id}", style=enums.ButtonStyle.SUCCESS)
    builder.add_row(
        types.InlineKeyboardButton("Prev", callback_data=f"shop_prev:{user_id}"),
        types.InlineKeyboardButton("Next", callback_data=f"shop_next:{user_id}")
    )
    builder.add_button("Back to Hub", callback_data="hub_main")
    markup = builder.build()
    try:
        if isinstance(message, types.CallbackQuery):
            await message.edit_message_media(
                media=types.InputMediaPhoto(media=char.img_url, caption=text, parse_mode=enums.ParseMode.HTML),
                reply_markup=markup
            )
        else:
            await reply_media_dynamic(message, char.img_url, caption=text,
                reply_markup=markup, parse_mode=enums.ParseMode.HTML
            )
    except errors.MessageNotModified:
        pass
    except errors.RPCError as e:
        LOGGER.error(f"Error in send_shop_message: {e}")
@app.on_callback_query(filters.regex(r"^shop_(prev|next):(\d+)$"))
@handle_errors
async def shop_navigation(_, query: types.CallbackQuery):
    action, user_id_str = query.data.split(":")
    user_id = int(user_id_str)
    if query.from_user.id != user_id:
        await query.answer("This shop session is not for you!", show_alert=True)
        return
    await query.answer()  # Dismiss spinner instantly
    session = await get_session(f"shop_{user_id}")
    if not session:
        await query.answer("Shop session expired. Use /shop again.", show_alert=True)
        return
    page = session["page"]
    chars_data = session["shop"]
    chars = [Character(**c) for c in chars_data]
    if "prev" in action:
        new_page = max(0, page - 1)
    else:
        new_page = min(len(chars) - 1, page + 1)
    session["page"] = new_page
    await create_session(f"shop_{user_id}", session)
    await send_shop_message(query, user_id)
@app.on_callback_query(filters.regex(r"^ask_buy_char_(.+)"))
@handle_errors
async def ask_buy_character(_, query: types.CallbackQuery):
    data = query.data.split("_")
    char_id = data[3]
    owner_id = int(data[4]) if len(data) > 4 else 0
    if owner_id and query.from_user.id != owner_id:
        return await query.answer("This is not your shop session!", show_alert=True)
    char_raw = await collection.find_one({"id": char_id})
    char = Character(**char_raw) if char_raw else None
    if not char:
        return await query.answer("Character not found.")
    price = RARITY_PRICES.get(char.rarity, 5)
    stock_limit = RARITY_STOCK_LIMITS.get(char.rarity, SHOP_LIMIT)
    sold_count = getattr(char, "sold_count", 0)
    text = (
        f"<b>Confirm Purchase</b>\n\n"
        f"<b>Name:</b> {html_escape(char.name)}\n"
        f"<b>Anime:</b> {html_escape(char.anime)}\n"
        f"<b>Rarity:</b> {html_escape(char.rarity)}\n"
        f"<b>ID:</b> <code>{char_id}</code>\n"
        f"<b>Stock:</b> <code>{sold_count}</code>/{stock_limit}\n\n"
        f"<b>Price:</b> <code>{price}</code> ⧫\n"
        f"Are you sure you want to buy this character?"
    )
    builder = KeyboardBuilder()
    builder.add_row(
        types.InlineKeyboardButton("Confirm Purchase", callback_data=f"confirm_buy_char_{char_id}_{query.from_user.id}", style=enums.ButtonStyle.SUCCESS),
        types.InlineKeyboardButton("Cancel", callback_data=f"shop_back_{query.from_user.id}", style=enums.ButtonStyle.DANGER)
    )
    await query.message.edit_caption(text, reply_markup=builder.build(), parse_mode=enums.ParseMode.HTML)
@app.on_callback_query(filters.regex(r"^confirm_buy_char_(.+)"))
@handle_errors
async def buy_character(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split("_")
    char_id = data[3]
    owner_id = int(data[4]) if len(data) > 4 else 0
    if owner_id and user_id != owner_id:
        return await query.answer("This is not your purchase!", show_alert=True)
    user_raw = await user_collection.find_one(get_user_filter(user_id))
    user_data = User(**user_raw) if user_raw else None
    owned = user_data.characters if user_data else []
    char_raw = await collection.find_one({"id": char_id})
    char = Character(**char_raw) if char_raw else None

    shop_chars = await get_daily_shop_characters()
    shop_ids = [c.id for c in shop_chars]

    if not char or char.id not in shop_ids:
        await query.answer("Character not available in today's shop.", show_alert=True)
        return

    owned_ids = [c.id if hasattr(c, "id") else (c["id"] if isinstance(c, dict) else c) for c in owned]
    if char_id in owned_ids:
        await query.answer("You already own this character!", show_alert=True)
        return
    price = RARITY_PRICES.get(char.rarity, 5)
    stock_limit = RARITY_STOCK_LIMITS.get(char.rarity, SHOP_LIMIT)
    user_zenith = user_data.zenith if user_data else 0
    if user_zenith < price:
        await query.answer(f"Insufficient Zenith!\nYou have: {user_zenith} ⧫\nNeed: {price} ⧫", show_alert=True)
        return
    update_result = await collection.update_one(
        {"id": char_id, "$or": [{"sold_count": {"$lt": stock_limit}}, {"sold_count": {"$exists": False}}]},
        {"$inc": {"sold_count": 1}}
    )
    if update_result.modified_count == 0:
        await query.answer("SOLD OUT! This character has reached the purchase limit.", show_alert=True)
        await query.message.edit_caption(f"<b>SOLD OUT</b>\n\nSomeone bought the last copy of {html_escape(char.name)}!", parse_mode=enums.ParseMode.HTML)
        return
    user_filt = get_user_filter(user_id)
    user_filt["zenith"] = {"$gte": price}
    user_filt["characters.id"] = {"$ne": char_id}
    from backend.core.rarities import rarity_id_of
    user_update = await user_collection.update_one(
        user_filt,
        {
            "$inc": {"zenith": -price, "char_count": 1, "version": 1},
            "$push": {"characters": {"id": char.id, "name": char.name, "anime": char.anime, "rarity": char.rarity, "rarity_id": rarity_id_of(char.rarity), "img_url": char.img_url}}
        }
    )
    if user_update.modified_count == 0:
        await collection.update_one({"id": char_id}, {"$inc": {"sold_count": -1}})
        await query.answer("Transaction failed. Insufficient Zenith or character already owned.", show_alert=True)
        return
    await update_quest_progress(user_id, "big_spender", price)
    await update_quest_progress(user_id, "weekly_spender", price)
    await check_achievements(user_id)
    await sync_user_to_redis(user_id)
    await query.message.edit_caption(
        f"<b>Purchase Successful!</b>\nYou now own <b>{char.name}</b>!\nRemaining Stock: <code>{getattr(char, 'sold_count', 0) + 1}</code>/{stock_limit}",
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer("Success!")
@app.on_message(filters.command("buylevel"))
@handle_errors
async def buy_level_cmd(_, message: types.Message):
    user_id = message.from_user.id
    try:
        levels = int(message.command[1]) if len(message.command) > 1 else 1
    except ValueError:
        return await message.reply_text("Usage: <code>/buylevel [amount]</code>\n\nExample: <code>/buylevel 5</code> to buy 5 levels.", parse_mode=enums.ParseMode.HTML)
    if levels < 1 or levels > 50:
        return await message.reply_text("Invalid amount (min 1, max 50 at a time).", parse_mode=enums.ParseMode.HTML)
    cost = levels * LEVEL_BUY_SHARD_COST

    # Atomic balance deduction
    res = await user_collection.update_one(
        {**get_user_filter(user_id), "balance": {"$gte": cost}},
        {"$inc": {"balance": -cost}}
    )

    if res.modified_count == 0:
        return await message.reply_text(f"You need <b>{cost:,}</b> ⬪ Shards to buy {levels} levels.", parse_mode=enums.ParseMode.HTML)
    from backend.core.progression import add_xp
    try:
        await add_xp(user_id, levels * 100, "shop_buylevel")
    except Exception as e:
        LOGGER.error(f"buy_level XP add failed for user {user_id}, rolling back: {e}")
        await user_collection.update_one(get_user_filter(user_id), {"$inc": {"balance": cost}})
        return await message.reply_text(
            "Transaction failed. Your shards have been refunded.",
            parse_mode=enums.ParseMode.HTML,
        )
    await update_quest_progress(user_id, "big_spender", cost)
    await update_quest_progress(user_id, "weekly_spender", cost)
    await check_achievements(user_id)
    await message.reply_text(f"<b>Levels Purchased!</b>\n\nSpent {cost:,} ⬪ Shards for +{levels * 100} XP.", parse_mode=enums.ParseMode.HTML)
