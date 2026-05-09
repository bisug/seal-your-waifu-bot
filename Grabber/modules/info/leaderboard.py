import html
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from Grabber import (LOGGER, WEB_APP_URL, app, group_user_totals_collection,
                     user_collection)
from Grabber.core.constants import METRIC_ORDER, METRICS
from Grabber.core.keyboard import get_webapp_button
from Grabber.core.progression import get_level_from_xp
from Grabber.core.utils import handle_errors, html_escape


# METRIC_ORDER and METRICS have been moved to Grabber.core.constants for centralization.
async def get_top_users(metric: str, limit: int = 10):
    from Grabber.core.cache import (_zset_key, get_cached_leaderboard, r,
                                    set_cached_leaderboard)
    from Grabber.database import user_collection
    # 1. Try to get fully populated list from string cache
    cached = await get_cached_leaderboard(metric, limit)
    if cached:
        return cached
    key = _zset_key(metric)
    if r:
        try:
            # 2. Try to get Top N from Redis ZSET
            uids = await r.zrevrange(key, 0, limit - 1, withscores=True)
            if uids:
                # Convert back to list of dicts. We need names and avatars, so we fetch from Mongo in ONE batch.
                user_ids = [int(u[0]) for u in uids]
                mongo_users = await user_collection.find({"id": {"$in": user_ids}}).to_list(length=limit)
                # Re-sort to match ZSET order and add the score
                user_map = {int(u["id"]): u for u in mongo_users}
                results = []
                for uid, score in uids:
                    u = user_map.get(int(uid))
                    if u:
                        u[METRICS[metric]["field"]] = int(score)
                        results.append(u)
                if results:
                    await set_cached_leaderboard(metric, results, limit)
                return results
        except Exception as e:
            LOGGER.warning(f"Redis ZSET leaderboard fetch failed for {metric}: {e}")
    # 2. Fallback to MongoDB aggregation if Redis fails or ZSET is empty
    field = METRICS[metric]["field"]
    pipeline = [
        {"$project": {"first_name": 1, "id": 1, "avatar": 1, "pass_type": 1, field: {"$ifNull": [f"${field}", 0]}}},
        {"$sort": {field: -1}},
        {"$limit": limit}
    ]
    cursor = await user_collection.aggregate(pipeline)
    results = await cursor.to_list(length=limit)
    # 3. Trigger background rebuild if ZSET was empty
    if r:
        import asyncio
        from Grabber.core.cache import rebuild_leaderboard
        asyncio.create_task(rebuild_leaderboard(user_collection, metric=metric))
    return results
def build_leaderboard_text(metric: str, users: list):
    info = METRICS[metric]
    text = f"<b>Global Leaderboard</b>\n"
    text += f"<b>Category:</b> {info['label']}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    if not users:
        text += "<i>No data available yet.</i>"
        return text
    for i, user in enumerate(users, 1):
        name = html_escape(user.get('first_name', 'User'))
        pass_type = user.get("pass_type", "free")
        if pass_type == "elite":
            name = f"{name} (Elite)"
        elif pass_type == "premium":
            name = f"{name} (Premium)"
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
            types.InlineKeyboardButton("«", callback_data=f"top_switch:{prev_metric}:{user_id}"),
            types.InlineKeyboardButton(METRICS[current_metric]['label'], callback_data="top_info"),
            types.InlineKeyboardButton("»", callback_data=f"top_switch:{next_metric}:{user_id}"),
        ]
    ]
    from Grabber.core.keyboard import get_webapp_button
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        buttons.append([webapp_btn])
    buttons.append([
        types.InlineKeyboardButton("Close", callback_data=f"top_close:{user_id}")
    ])
    return types.InlineKeyboardMarkup(buttons)
@app.on_message(filters.command("top"))
@handle_errors
async def global_leaderboard_handler(_, message: types.Message):
    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    users = await get_top_users("harem")
    text = build_leaderboard_text("harem", users)
    is_private = message.chat.type == enums.ChatType.PRIVATE
    keyboard = build_leaderboard_keyboard("harem", message.from_user.id, is_private)
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
@app.on_callback_query(filters.regex(r"^top_switch:"))
async def leaderboard_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    metric = data[1]
    owner_id = int(data[2])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your leaderboard!", show_alert=True)
    users = await get_top_users(metric)
    text = build_leaderboard_text(metric, users)
    is_private = query.message.chat.type == enums.ChatType.PRIVATE
    keyboard = build_leaderboard_keyboard(metric, owner_id, is_private)
    try:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    await query.answer()
@app.on_callback_query(filters.regex(r"^top_close:"))
async def leaderboard_close_callback(_, query: types.CallbackQuery):
    owner_id = int(query.data.split(":")[1])
    if query.from_user.id != owner_id:
        return await query.answer("This is not your leaderboard!", show_alert=True)
    await query.message.delete()
    await query.answer("Leaderboard closed.")
@app.on_callback_query(filters.regex(r"^top_info$"))
async def leaderboard_info_callback(_, query: types.CallbackQuery):
    await query.answer("Use arrows to switch categories!", show_alert=False)
@app.on_message(filters.command("ctop") & filters.group)
@handle_errors
async def chat_leaderboard_handler(_, message: types.Message):
    chat_id = message.chat.id
    from Grabber.core.cache import rget, rset
    # 1. Try Chat Cache (10 minute TTL)
    cache_key = f"ctop_text:{chat_id}"
    cached_text = await rget(cache_key)
    if cached_text:
        return await message.reply_text(cached_text, parse_mode=enums.ParseMode.HTML)
    await app.send_chat_action(chat_id, enums.ChatAction.TYPING)
    cursor = await group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    top_members = await cursor.to_list(length=10)
    if not top_members:
        return await message.reply_text("No data yet for this group.", parse_mode=enums.ParseMode.HTML)
    user_ids = [m["user_id"] for m in top_members]
    user_map = {}
    # 2. Strategy: Attempt to resolve names from DB first to save Telegram API calls
    mongo_users = await user_collection.find({"id": {"$in": user_ids}}, {"id": 1, "first_name": 1}).to_list(length=10)
    for u in mongo_users:
        user_map[int(u["id"])] = u.get("first_name", "User")
    # 3. Fallback for missing names: Bulk Telegram API call
    missing_ids = [uid for uid in user_ids if uid not in user_map]
    if missing_ids:
        try:
            fetched = await app.get_users(missing_ids)
            if not isinstance(fetched, list):
                fetched = [fetched]
            for u in fetched:
                user_map[u.id] = u.first_name
        except Exception:
            pass
    text = f"<b>Top Members in {html_escape(message.chat.title)}</b>\n\n"
    for i, member in enumerate(top_members, 1):
        uid = member['user_id']
        name = html_escape(user_map.get(uid, f"User {uid}"))
        text += f"{i}. {name} ➾ <b>{member['count']}</b>\n"
    # 4. Save to cache
    await rset(cache_key, text, 600)
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
