import html
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber.core.utils import html_escape
from Grabber import app
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
                                                        
    if metric == "harem":
        pipeline = [
            {"$project": {"first_name": 1, "id": 1, "char_count": {"$size": {"$ifNull": ["$characters", []]}}}},
            {"$sort": {"char_count": -1}},
            {"$limit": limit}
        ]
    else:
        field = METRICS[metric]["field"]
        pipeline = [
            {"$project": {"first_name": 1, "id": 1, field: {"$ifNull": [f"${field}", 0]}}},
            {"$sort": {field: -1}},
            {"$limit": limit}
        ]
    
    cursor = user_collection.aggregate(pipeline)
    return await cursor.to_list(length=limit)

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

def build_leaderboard_keyboard(current_metric: str, user_id: int):
                                                             
    idx = METRIC_ORDER.index(current_metric)
    prev_metric = METRIC_ORDER[(idx - 1) % len(METRIC_ORDER)]
    next_metric = METRIC_ORDER[(idx + 1) % len(METRIC_ORDER)]
    
    buttons = [
        [
            types.InlineKeyboardButton("⬅️", callback_data=f"top_switch:{prev_metric}:{user_id}"),
            types.InlineKeyboardButton(METRICS[current_metric]['label'], callback_data="top_info"),
            types.InlineKeyboardButton("➡️", callback_data=f"top_switch:{next_metric}:{user_id}"),
        ],
        [
            types.InlineKeyboardButton("❌ Close", callback_data=f"top_close:{user_id}")
        ]
    ]
    return types.InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("top"))
async def global_leaderboard_handler(_, message: types.Message):
    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    
                                  
    users = await get_top_users("harem")
    text = build_leaderboard_text("harem", users)
    keyboard = build_leaderboard_keyboard("harem", message.from_user.id)
    
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
    keyboard = build_leaderboard_keyboard(metric, owner_id)
    
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
    
    text = f"🏆 <b>Top Members in {html_escape(message.chat.title)}</b>\n\n"
    for i, member in enumerate(top_members, 1):
        user_id = member['user_id']
        try:
            m = await app.get_users(user_id)
            name = m.first_name
        except Exception:
            name = f"User {user_id}"
        
        text += f"{i}. {html_escape(name)} ➾ <b>{member['count']}</b>\n"
        
    await message.reply_text(text, parse_mode=ParseMode.HTML)
