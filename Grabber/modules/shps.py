import random
import httpx
from pyrogram import filters, types, enums, errors
from Grabber import app, collection, user_collection, sudo_users, OWNER_ID, LOGGER
from config import config
from Grabber.core.sessions import create_session, get_session

# === Configuration ===
EXTOL_API_KEY =""
EXTOL_RECEIVER = config.EXTOL_RECEIVER
SHOP_RARITY = "🪽 Shop"
DEFAULT_PRICE = 50  # Extols
SHOP_PAGE_SIZE = 5
ADMINS = list(set(sudo_users + [OWNER_ID]))

# === Extol API ===
async def get_extol_balance():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://marketapi.animerealms.org/api/balance",
                               headers={"api-key": EXTOL_API_KEY}, timeout=30)
        return resp.json()

async def withdraw_extol(amount, to):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://marketapi.animerealms.org/api/withdraw",
                               headers={"api-key": EXTOL_API_KEY},
                               params={"amount": amount, "address": to}, timeout=30)
        return resp.json()

# === Character Shop ===
async def get_daily_shop_characters():
    characters = await collection.find({"rarity": SHOP_RARITY}).to_list(None)
    if not characters:
        return []
    return random.sample(characters, min(len(characters), SHOP_PAGE_SIZE))

@app.on_message(filters.command("cshop"))
async def cshop_cmd(_, message: types.Message):
    chars = await get_daily_shop_characters()
    if not chars:
        await message.reply_text("🚫 No shop characters available.")
        return

    user_id = message.from_user.id
    # Use MongoDB for shop sessions
    await create_session(f"shop_{user_id}", {"shop": chars, "page": 0})
    await send_shop_message(message, user_id)

# --- NEW SHOP HUB ---
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

    if isinstance(message_or_query, types.CallbackQuery):
        await message_or_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await message_or_query.reply_text(text, reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^hub_(char|pet|pass|egg|main)$"))
async def hub_callback_handler(_, query: types.CallbackQuery):
    choice = query.data.split("_")[1]
    
    if choice == "main":
        await send_shop_hub(query)
    elif choice == "char":
        chars = await get_daily_shop_characters()
        if not chars:
            return await query.answer("🚫 No shop characters available.", show_alert=True)
        await create_session(f"shop_{query.from_user.id}", {"shop": chars, "page": 0})
        await send_shop_message(query, query.from_user.id)
    elif choice == "pet":
        import Grabber.modules.pet as pet_module
        await pet_module.send_petshop_page(query, 0)
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
    chars = session.get("shop", [])
    
    char = chars[page]
    price = char.get("price", DEFAULT_PRICE)
    balance_data = await get_extol_balance()
    balance = balance_data.get("balance", 0)

    text = (
        f"🛍️ **Character Shop**\n"
        f"💰 **Extol Balance:** {balance} EXT\n\n"
        f"🆔 **ID:** {char['id']}\n"
        f"📛 **Name:** {char['name']}\n"
        f"📺 **Anime:** {char['anime']}\n"
        f"🏷 **Rarity:** {char['rarity']}\n"
        f"💲 **Price:** {price} EXT"
    )

    keyboard = [
        [types.InlineKeyboardButton("💰 Buy", callback_data=f"ask_buy_char_{char['id']}")],
        [
            types.InlineKeyboardButton("⬅️ Prev", callback_data=f"shop_prev:{user_id}"),
            types.InlineKeyboardButton("➡️ Next", callback_data=f"shop_next:{user_id}")
        ],
        [types.InlineKeyboardButton("⤾ Back to Hub", callback_data="hub_main")]
    ]

    markup = types.InlineKeyboardMarkup(keyboard)

    try:
        if isinstance(message, types.CallbackQuery):
            await message.message.edit_media(
                media=types.InputMediaPhoto(media=char["img_url"], caption=text, parse_mode=enums.ParseMode.MARKDOWN),
                reply_markup=markup
            )
        else:
            await message.reply_photo(
                photo=char["img_url"], caption=text,
                reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN
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
    chars = session["shop"]

    if "prev" in action:
        new_page = max(0, page - 1)
    else:
        new_page = min(len(chars) - 1, page + 1)

    # Update session in MongoDB
    session["page"] = new_page
    await create_session(f"shop_{user_id}", session)

    await send_shop_message(query, user_id)
    await query.answer()

@app.on_callback_query(filters.regex(r"^ask_buy_char_(.+)"))
async def ask_buy_character(_, query: types.CallbackQuery):
    char_id = query.data.split("_")[3]
    char = await collection.find_one({"id": char_id})
    if not char:
        return await query.answer("❌ Character not found.")
    
    price = char.get("price", DEFAULT_PRICE)
    text = (
        f"⚠️ **Confirm Purchase**\n\n"
        f"Are you sure you want to buy **{char['name']}** for **{price} EXT**?"
    )
    keyboard = [
        [
            types.InlineKeyboardButton("Confirm ✅", callback_data=f"confirm_buy_char_{char_id}"),
            types.InlineKeyboardButton("Cancel ❌", callback_data="hub_char")
        ]
    ]
    await query.message.edit_caption(text, reply_markup=types.InlineKeyboardMarkup(keyboard))

@app.on_callback_query(filters.regex(r"^confirm_buy_char_(.+)"))
async def buy_character(_, query: types.CallbackQuery):
    user_id = query.from_user.id
    char_id = query.data.split("_")[3]

    user_data = await user_collection.find_one({"id": user_id}) or {}
    owned = user_data.get("characters", [])

    char = await collection.find_one({"id": char_id})
    if not char or char["rarity"] != SHOP_RARITY:
        await query.answer("❌ Character not available.", show_alert=True)
        return

    owned_ids = [c["id"] if isinstance(c, dict) else c for c in owned]
    if char_id in owned_ids:
        await query.answer("✅ You already own this character.", show_alert=True)
        return

    price = char.get("price", DEFAULT_PRICE)
    
    try:
        payment = await withdraw_extol(price, EXTOL_RECEIVER)
        if not payment.get("ok"):
            await query.answer(f"❌ Payment failed: {payment.get('error', 'unknown error')}", show_alert=True)
            return
    except Exception as e:
        LOGGER.error(f"Extol API error: {e}")
        await query.answer("❌ API Error. Try again later.", show_alert=True)
        return

    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"id": user_id},
            "$push": {"characters": {
                "id": char["id"],
                "name": char["name"],
                "anime": char["anime"],
                "rarity": char["rarity"],
                "img_url": char["img_url"]
            }}
        },
        upsert=True
    )

    await query.message.reply_text(
        f"✅ **Purchase Successful!**\n🎉 You now own **{char['name']}**!",
        parse_mode=enums.ParseMode.MARKDOWN
    )
    await query.answer("Success!")

@app.on_message(filters.command("balances"))
async def balance_command(_, message: types.Message):
    try:
        data = await get_extol_balance()
        if not data or not data.get("ok"):
            await message.reply_text("❌ Could not retrieve balance.")
            return

        balance = data.get("balance", 0)
        address = data.get("address", "Unknown")
        await message.reply_text(
            f"💳 **Extol Balance:** {balance} EXT\n🏦 **Address:** `{address}`",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        LOGGER.error(f"Balance check error: {e}")
        await message.reply_text("❌ API connection failed.")

@app.on_message(filters.command("setpr") & filters.user(ADMINS))
async def set_price(_, message: types.Message):
    if len(message.command) != 3:
        return await message.reply_text("❌ Usage: <code>/setpr &lt;id&gt; &lt;price&gt;</code>", parse_mode=enums.ParseMode.HTML)
        return

    try:
        char_id, price = message.command[1], int(message.command[2])
        await collection.update_one({"id": char_id}, {"$set": {"price": price}})
        await message.reply_text(f"✅ Price updated: {char_id} → {price} EXT")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
