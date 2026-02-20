import random
import httpx
from pyrogram.enums import ParseMode
from pyrogram import filters, types, errors, enums
from Grabber.core.utils import md_escape
from Grabber import app, collection, user_collection, sudo_users, OWNER_ID, LOGGER
from Grabber.models import Character, User
from config import config
from Grabber.core.sessions import create_session, get_session
from Grabber.modules.rarities import RARITY_MAP
from Grabber.modules.quests import update_quest_progress
from Grabber.modules.achievements import check_achievements

                       
SHOP_RARITY = RARITY_MAP[8]         
DEFAULT_ZENITH_PRICE = 5                        
SHOP_PAGE_SIZE = 5
SHOP_LIMIT = 20                             
ADMINS = list(set(sudo_users + [OWNER_ID]))
SHOP_BANNER = config.PHOTO_URL[0]

                        
async def get_daily_shop_characters():
    cursor = collection.find({"rarity": SHOP_RARITY})
    characters_raw = await cursor.to_list(None)
    if not characters_raw:
        return []
    characters = [Character(**c) for c in characters_raw]
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

@app.on_message(filters.command("cshop"))
async def cshop_cmd(_, message: types.Message):
    chars = await get_daily_shop_characters()
    if not chars:
        await message.reply_text("🚫 No shop characters available.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    user_id = message.from_user.id
                                   
    # Serialize Character objects to dicts for MongoDB
    chars_data = [c.dict() for c in chars]
    await create_session(f"shop_{user_id}", {"shop": chars_data, "page": 0})
    await send_shop_message(message, user_id)

                      
@app.on_message(filters.command("shop"))
async def shop_hub(_, message: types.Message):
    await send_shop_hub(message)

async def send_shop_hub(message_or_query):
    text = (
        "🏪 **Seal Shop Central**\n\n"
        "Welcome to the marketplace! Choose a category below to start browsing."
    )
    keyboard = [
        [types.InlineKeyboardButton("👤 Character Shop", callback_data="hub_char")],
        [types.InlineKeyboardButton("🐾 Pet Shop", callback_data="hub_pet")],
        [types.InlineKeyboardButton("🎫 Battle Pass", callback_data="hub_pass")],
        [types.InlineKeyboardButton("🥚 Egg Shop", callback_data="hub_egg")]
    ]
    reply_markup = types.InlineKeyboardMarkup(keyboard)

    try:
        if isinstance(message_or_query, types.CallbackQuery):
            await message_or_query.edit_message_media(
                media=types.InputMediaPhoto(media=SHOP_BANNER, caption=text, parse_mode=ParseMode.MARKDOWN_V2),
                reply_markup=reply_markup
            )
        else:
            await message_or_query.reply_photo(
                photo=SHOP_BANNER, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2
            )
    except Exception as e:
        LOGGER.error(f"Error in send_shop_hub: {e}")
                                                                  
        if isinstance(message_or_query, types.CallbackQuery):
            try:
                await message_or_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
            except:
                pass
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)

@app.on_callback_query(filters.regex(r"^hub_(char|pet|pass|egg|main)$"))
async def hub_callback_handler(_, query: types.CallbackQuery):
    choice = query.data.split("_")[1]
    
    if choice == "main":
        await send_shop_hub(query)
    elif choice == "char":
        chars = await get_daily_shop_characters()
        if not chars:
            return await query.answer("🚫 No shop characters available.", show_alert=True)
        # Serialize Character objects to dicts for MongoDB
        chars_data = [c.dict() for c in chars]
        await create_session(f"shop_{query.from_user.id}", {"shop": chars_data, "page": 0})
        await send_shop_message(query, query.from_user.id)
    elif choice == "pet":
        import Grabber.modules.pet as pet_module
        await pet_module.send_petshop_page(query, 0, query.from_user.id)
    elif choice == "pass":
        import Grabber.modules.battlepass as pass_module
        await pass_module.view_pass_inline(query)
    elif choice == "egg":
        import Grabber.modules.hunt as hunt_module
        await hunt_module.show_egg_page(query, 0, query.from_user.id)
    
    await query.answer()

async def send_shop_message(message, user_id):
    session = await get_session(f"shop_{user_id}")
    if not session:
        return

    page = session.get("page", 0)
    page = session.get("page", 0)
    chars_data = session.get("shop", [])
    # Deserialize back to Character objects
    chars = [Character(**c) for c in chars_data]
    
    char = chars[page]
    price = getattr(char, "zenith_price", DEFAULT_ZENITH_PRICE)
    
                               
    user_raw = await user_collection.find_one({"id": user_id})
    user = User(**user_raw) if user_raw else None
    zenith_balance = user.zenith if user else 0

                 
    sold_count = getattr(char, "sold_count", 0)
    stock_display = f"{sold_count}/{SHOP_LIMIT}"
    if sold_count >= SHOP_LIMIT:
        stock_display = "❌ SOLD OUT"

    text = (
        f"🛍️ **Character Shop**\n"
        f"⧫ **Zenith Balance:** {zenith_balance:,}\n\n"
        f"🆔 **ID:** {char.id}\n"
        f"📛 **Name:** {char.name}\n"
        f"📺 **Anime:** {char.anime}\n"
        f"🏷 **Rarity:** {char.rarity}\n"
        f"� **Stock:** {stock_display}\n"
        f"�💲 **Price:** {price} ⧫"
    )

    keyboard = [
        [types.InlineKeyboardButton("💰 Buy", callback_data=f"ask_buy_char_{char.id}")],
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev:{user_id}"),
            types.InlineKeyboardButton("➡️ Next", callback_data=f"shop_next:{user_id}")
        ],
        [types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")]
    ]

    markup = types.InlineKeyboardMarkup(keyboard)

    try:
        if isinstance(message, types.CallbackQuery):
            await message.edit_message_media(
                media=types.InputMediaPhoto(media=char.img_url, caption=text, parse_mode=ParseMode.MARKDOWN_V2),
                reply_markup=markup
            )
        else:
            await message.reply_photo(
                photo=char.img_url, caption=text,
                reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2
            )
    except errors.MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(f"Error in send_shop_message: {e}")

@app.on_callback_query(filters.regex(r"^shop_(prev|next):(\d+)$"))
async def shop_navigation(_, query: types.CallbackQuery):
    action, user_id_str = query.data.split(":")
    user_id = int(user_id_str)

    if query.from_user.id != user_id:
        await query.answer("❌ This shop session is not for you!", show_alert=True)
        return

    session = await get_session(f"shop_{user_id}")
    if not session:
        await query.answer("🚫 Shop session expired. Use /shop again.", show_alert=True)
        return

    page = session["page"]
    page = session["page"]
    chars_data = session["shop"]
    # Deserialize back to Character objects
    chars = [Character(**c) for c in chars_data]

    if "prev" in action:
        new_page = max(0, page - 1)
    else:
        new_page = min(len(chars) - 1, page + 1)

                               
    session["page"] = new_page
    await create_session(f"shop_{user_id}", session)

    await send_shop_message(query, user_id)
    await query.answer()

@app.on_callback_query(filters.regex(r"^ask_buy_char_(.+)"))
async def ask_buy_character(_, query: types.CallbackQuery):
    char_id = query.data.split("_")[3]
    char_raw = await collection.find_one({"id": char_id})
    char = Character(**char_raw) if char_raw else None
    if not char:
        return await query.answer("❌ Character not found.")
    
    price = getattr(char, "zenith_price", DEFAULT_ZENITH_PRICE)
    
    sold_count = getattr(char, "sold_count", 0)
    stock_status = "✅ In Stock" if sold_count < SHOP_LIMIT else "❌ SOLD OUT"
    
    text = (
        f"⚠️ **Confirm Purchase**\n\n"
        f"👤 **Name:** {md_escape(char.name)}\n"
        f"📺 **Anime:** {md_escape(char.anime)}\n"
        f"🏷 **Rarity:** {md_escape(char.rarity)}\n"
        f"🆔 **ID:** `{char_id}`\n"
        f"📦 **Stock:** {sold_count}/{SHOP_LIMIT}\n\n"
        f"💰 **Price:** {price} ⧫\n"
        f"Are you sure you want to buy this character?"
    )
    keyboard = [
        [
            types.InlineKeyboardButton("Confirm ✅", callback_data=f"confirm_buy_char_{char_id}"),
            types.InlineKeyboardButton("Cancel ❌", callback_data="hub_char")
        ]
    ]
    await query.message.edit_caption(text, reply_markup=types.InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)

@app.on_callback_query(filters.regex(r"^confirm_buy_char_(.+)"))
async def buy_character(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    char_id = query.data.split("_")[3]

    user_raw = await user_collection.find_one({"id": user_id})
    user_data = User(**user_raw) if user_raw else None
    owned = user_data.characters if user_data else []

    char_raw = await collection.find_one({"id": char_id})
    char = Character(**char_raw) if char_raw else None
    if not char or char.rarity != SHOP_RARITY:
        await query.answer("❌ Character not available.", show_alert=True)
        return

    owned_ids = [c.id if hasattr(c, "id") else (c["id"] if isinstance(c, dict) else c) for c in owned]
    if char_id in owned_ids:
        await query.answer("✅ You already own this character.", show_alert=True)
        return

    price = getattr(char, "zenith_price", DEFAULT_ZENITH_PRICE)
    
                          
    user_zenith = user_data.zenith if user_data else 0
    if user_zenith < price:
        await query.answer(
            f"❌ Insufficient Zenith!\n\nYou have: {user_zenith} ⧫\nNeed: {price} ⧫",
            show_alert=True
        )
        return
    
                                      
                                                               
                                                                                  
    update_result = await collection.update_one(
        {
            "id": char_id,
            "$or": [
                {"sold_count": {"$lt": SHOP_LIMIT}},
                {"sold_count": {"$exists": False}}
            ]
        },
        {"$inc": {"sold_count": 1}}
    )

    if update_result.modified_count == 0:
        await query.answer("❌ SOLD OUT! This character has reached the purchase limit.", show_alert=True)
        await query.message.edit_caption(fr"❌ **SOLD OUT**\n\nSomeone bought the last copy of {md_escape(char.name)}\!", parse_mode=ParseMode.MARKDOWN_V2)
        return

                   
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"zenith": -price}}
    )

    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"id": user_id},
            "$push": {"characters": {
                "id": char.id,
                "name": char.name,
                "anime": char.anime,
                "rarity": char.rarity,
                "img_url": char.img_url
            }}
        },
        upsert=True
    )
    
                  
    await update_quest_progress(user_id, "big_spender", price)
    
                        
    await check_achievements(user_id)

    await query.message.reply_text(
        f"✅ **Purchase Successful!**\n🎉 You now own **{char.name}**!\n📦 Stock: {getattr(char, 'sold_count', 0) + 1}/{SHOP_LIMIT}",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await query.answer("Success!")


