from pymongo import ReturnDocument
from pyrogram import types

from config import config
from backend import game_bot, sessions_collection, user_collection
from backend.core.cache import get_cached_user, sync_user_to_redis
from backend.core.user import add_user_set_on_insert, get_user_filter
from backend.core.utils import check_member_requirement, html_escape


async def send_requirement_failure(message: types.Message, reason: str, count: int = 0):
    if reason == "group_only":
        text = "❌ <b>Group Required:</b> This game can only be played in group chats."
    elif reason == "member_count":
        text = (
            "⚠️ <b>Security Level Low:</b> This sector must contain at least "
            "<b>50 personnel</b> (members) to authorize GameBot operations.\n\n"
            f"Current count: <code>{count}</code>"
        )
    else:
        from backend import BOT_NAME, BOT_USERNAME

        text = (
            f"🚫 <b>Main Bot Missing:</b> GameBot operations require the presence of "
            f"<b>{BOT_NAME}</b> (@{BOT_USERNAME}) in this sector.\n\n"
            "<i>Please add the Main Bot to authorize games!</i>"
        )
    await game_bot.send_message_safe(message.chat.id, text, auto_delete=300)


async def ensure_registered_user(user: types.User, chat_id: int) -> bool:
    cached = await get_cached_user(user.id)
    if cached is not None:
        return True

    db_user = await user_collection.find_one(get_user_filter(user.id), {"id": 1})
    if db_user:
        return True

    markup = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton(
            "🚀 Start Bot in DM",
            url=f"https://t.me/{config.BOT_USERNAME}?start=true",
        )
    ]])
    text = (
        "❌ <b>Access Denied!</b>\n\n"
        f"<a href='tg://user?id={user.id}'>{html_escape(user.first_name)}</a>, "
        "you must start the bot in private messages first to play and earn shards!"
    )
    await game_bot.send_message_safe(chat_id, text=text, reply_markup=markup, auto_delete=30)
    return False


async def ensure_gamebot_ready(message: types.Message, *, require_registered: bool = True) -> bool:
    if not message.from_user:
        return False

    meets_req, reason, count = await check_member_requirement(game_bot, message.chat)
    if not meets_req:
        await send_requirement_failure(message, reason, count)
        return False

    if require_registered:
        return await ensure_registered_user(message.from_user, message.chat.id)
    return True


async def award_gamebot_shards(
    user: types.User,
    amount: int,
    *,
    extra_inc: dict | None = None,
    game_key: str | None = None,
) -> dict:
    inc = {"balance": int(amount), "gamebot_earned": int(amount), "gamebot_wins": 1, "version": 1}
    if extra_inc:
        inc.update({key: int(value) for key, value in extra_inc.items()})

    update = {
        "$set": {
            "first_name": user.first_name,
            "username": user.username,
        },
        "$inc": inc,
    }
    updated = await user_collection.find_one_and_update(
        get_user_filter(user.id),
        add_user_set_on_insert(
            update,
            user.id,
            first_name=user.first_name,
            username=user.username,
        ),
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    if game_key:
        await sessions_collection.update_one(
            {"id": "gamebot_global_stats"},
            {"$inc": {f"{game_key}_wins": 1, "total_rewards": int(amount)}},
            upsert=True,
        )

    await sync_user_to_redis(user.id, updated)
    return updated or {}
