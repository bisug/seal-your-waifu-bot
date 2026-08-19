import html
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from config import config
from backend import (LOGGER, WEB_APP_URL, app, group_user_totals_collection,
                     user_collection)
from backend.core.constants import METRIC_ORDER, METRICS
from backend.core.keyboard import get_webapp_button
from backend.core.progression import get_level_from_xp
from backend.core.tasks import run_background_task
from backend.core.utils import handle_errors, html_escape


# METRIC_ORDER and METRICS have been moved to backend.core.constants for centralization.
def _user_id_variants(user_id) -> list:
    variants = []
    if user_id is None:
        return variants

    variants.append(user_id)
    try:
        uid_int = int(user_id)
        variants.extend([uid_int, str(uid_int)])
    except (TypeError, ValueError):
        variants.append(str(user_id))

    deduped = []
    for value in variants:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _needs_name_resolution(user: dict) -> bool:
    first_name = str(user.get("first_name") or "").strip()
    return not first_name or first_name.lower() == "user"


async def _hydrate_leaderboard_profiles(users: list, metric: str) -> list:
    """Merge leaderboard rows with Mongo profile fields while preserving rank order."""
    if not users:
        return users

    from backend.database import user_collection

    lookup_values = []
    for user in users:
        lookup_values.extend(_user_id_variants(user.get("id")))

    if not lookup_values:
        return users

    projection = {
        "id": 1,
        "first_name": 1,
        "last_name": 1,
        "username": 1,
        "avatar": 1,
        "pass_type": 1,
        METRICS[metric]["field"]: 1,
    }
    mongo_users = await user_collection.find({"id": {"$in": lookup_values}}, projection).to_list(length=len(lookup_values))

    profile_map = {}
    for profile in mongo_users:
        for variant in _user_id_variants(profile.get("id")):
            profile_map[str(variant)] = profile

    hydrated = []
    for user in users:
        profile = None
        for variant in _user_id_variants(user.get("id")):
            profile = profile_map.get(str(variant))
            if profile:
                break

        if profile:
            merged = {**user}
            for key in ("first_name", "last_name", "username", "avatar", "pass_type"):
                if profile.get(key):
                    merged[key] = profile[key]
            hydrated.append(merged)
        else:
            hydrated.append(user)

    return hydrated


async def _resolve_missing_names(users: list) -> list:
    """
    For any user in the list without a first_name, attempt to resolve it via
    the Telegram API and persist the result back to MongoDB for future calls.
    """
    from backend.database import user_collection
    missing = [u for u in users if _needs_name_resolution(u) and u.get("id")]
    if not missing:
        return users
    missing_ids = [int(u["id"]) for u in missing]
    try:
        fetched = await app.get_users(missing_ids)
        if not isinstance(fetched, list):
            fetched = [fetched]
        user_info_map = {
            u.id: {
                "first_name": u.first_name,
                "last_name": u.last_name,
                "username": u.username
            } for u in fetched if u.first_name
        }
        # Persist resolved names back to DB in the background
        for uid, info in user_info_map.items():
            await user_collection.update_many(
                {"id": {"$in": [uid, str(uid)]}},
                {"$set": info}
            )
        # Patch the results in-place
        for u in users:
            if _needs_name_resolution(u):
                resolved = user_info_map.get(int(u["id"]))
                if resolved:
                    u.update(resolved)
    except Exception as e:
        LOGGER.warning(f"_resolve_missing_names: Telegram API fallback failed: {e}")
    return users

async def get_top_users(metric: str, limit: int = 10):
    from backend.core.cache import (_zset_key, get_cached_leaderboard, r,
                                    set_cached_leaderboard)
    from backend.database import user_collection
    # 1. Try to get fully populated list from string cache
    cached = await get_cached_leaderboard(metric, limit)
    if cached:
        cached = await _hydrate_leaderboard_profiles(cached, metric)
        cached = await _resolve_missing_names(cached)
        await set_cached_leaderboard(metric, cached, limit)
        return cached
    key = _zset_key(metric)
    if r:
        try:
            # 2. Try to get Top N from Redis ZSET
            uids = await r.zrevrange(key, 0, limit - 1, withscores=True)
            if uids:
                # Filter out any None/corrupt entries before casting to int
                valid_uids = [(uid, score) for uid, score in uids if uid is not None]
                # Convert back to list of dicts. We need names and avatars, so we fetch from Mongo in ONE batch.
                user_ids = []
                for uid, _ in valid_uids:
                    user_ids.extend(_user_id_variants(uid))
                mongo_users = await user_collection.find({"id": {"$in": user_ids}}).to_list(length=len(user_ids))
                # Re-sort to match ZSET order and add the score
                user_map = {}
                for user in mongo_users:
                    for variant in _user_id_variants(user.get("id")):
                        user_map[str(variant)] = user
                results = []
                for uid, score in valid_uids:
                    u = None
                    for variant in _user_id_variants(uid):
                        u = user_map.get(str(variant))
                        if u:
                            break
                    if u:
                        row = {**u, METRICS[metric]["field"]: int(score)}
                        results.append(row)
                if results:
                    results = await _hydrate_leaderboard_profiles(results, metric)
                    results = await _resolve_missing_names(results)
                    await set_cached_leaderboard(metric, results, limit)
                return results
        except Exception as e:
            LOGGER.warning(f"Redis ZSET leaderboard fetch failed for {metric}: {e}")
    # 2. Fallback to MongoDB aggregation if Redis fails or ZSET is empty
    field = METRICS[metric]["field"]
    pipeline = [
        {"$project": {
            "first_name": 1,
            "last_name": 1,
            "username": 1,
            "id": 1,
            "avatar": 1,
            "pass_type": 1,
            field: {"$ifNull": [f"${field}", 0]}
        }},
        {"$sort": {field: -1}},
        {"$limit": limit}
    ]
    cursor = await user_collection.aggregate(pipeline)
    results = await cursor.to_list(length=limit)
    results = await _resolve_missing_names(results)
    # 3. Trigger background rebuild if ZSET was empty
    if r:
        from backend.core.cache import rebuild_leaderboard
        run_background_task(rebuild_leaderboard(user_collection, metric=metric))

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
        uid = user.get("id")
        first_name = user.get('first_name', 'User')
        last_name = user.get('last_name')
        full_name = f"{first_name} {last_name}" if last_name else first_name
        mention = f'<a href="tg://user?id={uid}">{html_escape(full_name)}</a>'

        pass_type = user.get("pass_type", "free")
        if pass_type == "elite":
            mention = f"{mention} (Elite)"
        elif pass_type == "premium":
            mention = f"{mention} (Premium)"

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
        text += f"{i}. {mention} ➾ <b>{display_value}</b>\n"
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
    from backend.core.keyboard import get_webapp_button
    webapp_btn = get_webapp_button(is_private, path="#leaderboard")
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
    from backend.core.cache import rget, rset
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
    mongo_users = await user_collection.find(
        {"id": {"$in": user_ids}},
        {"id": 1, "first_name": 1, "last_name": 1}
    ).to_list(length=10)
    for u in mongo_users:
        first_name = u.get("first_name", "User")
        last_name = u.get("last_name")
        full_name = f"{first_name} {last_name}" if last_name else first_name
        user_map[int(u["id"])] = full_name
    # 3. Fallback for missing names: Bulk Telegram API call
    missing_ids = [uid for uid in user_ids if uid not in user_map]
    if missing_ids:
        try:
            fetched = await app.get_users(missing_ids)
            if not isinstance(fetched, list):
                fetched = [fetched]
            for u in fetched:
                first_name = u.first_name or "User"
                last_name = u.last_name
                full_name = f"{first_name} {last_name}" if last_name else first_name
                user_map[u.id] = full_name
        except Exception:
            pass
    text = f"<b>Top Members in {html_escape(message.chat.title)}</b>\n\n"
    for i, member in enumerate(top_members, 1):
        uid = member['user_id']
        name = html_escape(user_map.get(uid, f"User {uid}"))
        mention = f'<a href="tg://user?id={uid}">{name}</a>'
        text += f"{i}. {mention} ➾ <b>{member['count']}</b>\n"
    # 4. Save to cache
    await rset(cache_key, text, 600)
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
