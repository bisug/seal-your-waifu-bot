import html
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app, WEB_APP_URL
from config import config
from Grabber import user_collection, top_global_groups_collection, group_user_totals_collection
from Grabber.core.progression import get_level_from_xp

METRIC_ORDER = ["harem", "shards", "zenith", "level", "guesses"]

METRICS = {
    "harem": {"label": "🎒 Harem", "field": "char_count", "icon": "🍱"},
    "shards": {"label": "⬪ Shards", "field": "balance", "icon": "⬪"},
    "zenith": {"label": "⧫ Zenith", "field": "zenith", "icon": "⧫"},
    "level": {"label": "⭐ Level", "field": "xp", "icon": "🆙"},
    "guesses": {"label": "🎯 Guesses", "field": "guess_count", "icon": "🎯"}
}

async def get_top_users(metric: str, limit: int = 10):
    from Grabber.core.cache import get_cached_leaderboard, set_cached_leaderboard

    # Try Redis cache first
    cached = await get_cached_leaderboard(metric)
    if cached is not None:
        return cached

    if metric == "harem":
        pipeline = [
            {"$project": {"first_name": 1, "id": 1, "avatar": 1, "char_count": {"$size": {"$ifNull": ["$characters", []]}}}},
            {"$sort": {"char_count": -1}},
            {"$limit": limit}
        ]
    else:
        field = METRICS[metric]["field"]
        pipeline = [
            {"$project": {"first_name": 1, "id": 1, "avatar": 1, field: {"$ifNull": [f"${field}", 0]}}},
            {"$sort": {field: -1}},
            {"$limit": limit}
        ]

    cursor = user_collection.aggregate(pipeline)
    results = await cursor.to_list(length=limit)

    # Cache the result
    await set_cached_leaderboard(metric, results)
    return results

def build_leaderboard_text(metric: str, users: list):

    info = METRICS[metric]
    text = f"🌐 <b>Global Leaderboard</b>\n"
    text += f"📊 <b>Category:</b> {info['label']}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not users:
        text += "<i>No data available yet.</i>"
        return text

    for i, user in enumerate(users, 1):
        name = html_escape(user.get('first_name', 'User'))
        value = user.get(info['field'], 0)


        if metric == "level":
            lvl = get_level_from_xp(value)
            display_value = f"Lvl {lvl}"
        elif metric == "shards":
            display_value = f"{value:,} ⬪"
        elif metric == "zenith":
            display_value = f"{value:,} ⧫"
        elif metric == "guesses":
            display_value = f"{value:,} Guesses"
        else:
            display_value = f"{value:,} Chars"

        text += f"{i}. {name} ➾ <b>{display_value}</b>\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━━"
    return text

def build_leaderboard_keyboard(current_metric: str, user_id: int, is_private: bool):

    idx = METRIC_ORDER.index(current_metric)
    prev_metric = METRIC_ORDER[(idx - 1) % len(METRIC_ORDER)]
    next_metric = METRIC_ORDER[(idx + 1) % len(METRIC_ORDER)]

    buttons = [
        [
            types.InlineKeyboardButton("⬅️", callback_data=f"top_switch:{prev_metric}:{user_id}"),
            types.InlineKeyboardButton(METRICS[current_metric]['label'], callback_data="top_info"),
            types.InlineKeyboardButton("➡️", callback_data=f"top_switch:{next_metric}:{user_id}"),
        ]
    ]

    if is_private:
        buttons.append([types.InlineKeyboardButton("🌐 Open Web App", web_app=types.WebAppInfo(url=WEB_APP_URL))])
    else:
        bot_username = getattr(config, "BOT_USERNAME", "Seal_Your_Waifu_Bot")
        buttons.append([types.InlineKeyboardButton("🌐 Launch Web App (DM)", url=f"https://t.me/{bot_username}?start=webapp")])

    buttons.append([
        types.InlineKeyboardButton("❌ Close", callback_data=f"top_close:{user_id}")
    ])
    
    return types.InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("top"))
async def global_leaderboard_handler(_, message: types.Message):
    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)


    users = await get_top_users("harem")
    text = build_leaderboard_text("harem", users)
    is_private = message.chat.type == enums.ChatType.PRIVATE
    keyboard = build_leaderboard_keyboard("harem", message.from_user.id, is_private)

    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^top_switch:"))
async def leaderboard_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    metric = data[1]
    owner_id = int(data[2])

    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your leaderboard!", show_alert=True)

    users = await get_top_users(metric)
    text = build_leaderboard_text(metric, users)
    is_private = query.message.chat.type == enums.ChatType.PRIVATE
    keyboard = build_leaderboard_keyboard(metric, owner_id, is_private)

    try:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await query.answer()

@app.on_callback_query(filters.regex(r"^top_close:"))
async def leaderboard_close_callback(_, query: types.CallbackQuery):
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("❌ This is not your leaderboard!", show_alert=True)

    await query.message.delete()
    await query.answer("Leaderboard closed.")

@app.on_callback_query(filters.regex(r"^top_info$"))
async def leaderboard_info_callback(_, query: types.CallbackQuery):
    await query.answer("Use arrows to switch categories!", show_alert=False)


@app.on_message(filters.command("ctop") & filters.group)
async def chat_leaderboard_handler(_, message: types.Message):
    chat_id = message.chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])

    top_members = await cursor.to_list(length=10)

    if not top_members:
        return await message.reply_text("⚠️ No data yet for this group.", parse_mode=ParseMode.HTML)

    # Batch fetch all users in a single API call instead of N sequential calls
    user_ids = [m["user_id"] for m in top_members]
    user_map = {}
    try:
        fetched = await app.get_users(user_ids)
        if not isinstance(fetched, list):
            fetched = [fetched]
        for u in fetched:
            user_map[u.id] = u.first_name
    except Exception:
        pass

    text = f"🏆 <b>Top Members in {html_escape(message.chat.title)}</b>\n\n"
    for i, member in enumerate(top_members, 1):
        uid = member['user_id']
        name = html_escape(user_map.get(uid, f"User {uid}"))
        text += f"{i}. {name} ➾ <b>{member['count']}</b>\n"

    await message.reply_text(text, parse_mode=ParseMode.HTML)
