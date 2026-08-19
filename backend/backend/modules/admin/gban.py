from pyrogram import ContinuePropagation, StopPropagation, enums, errors, filters, types

from backend import LOGGER, app, game_bot, sudo_filter
from backend.core.global_bans import (
    add_group_gban,
    add_user_gban,
    get_group_gban,
    get_user_gban,
    remove_group_gban,
    remove_user_gban,
)
from backend.core.roles import moderator
from backend.core.utils import get_now_utc, handle_errors, html_escape
from backend.database import (
    global_group_bans_collection,
    global_user_bans_collection,
    group_collection,
)

DEFAULT_REASON = "No reason provided."
MAX_REASON_LEN = 300
GROUP_CHAT_TYPES = {enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL}
PRIVATE_CHAT_TYPES = {enums.ChatType.PRIVATE, enums.ChatType.BOT}

_notified_banned_chats: set[tuple[str, int]] = set()


def _is_privileged(user_id: int | None) -> bool:
    return moderator(user_id)


def _reason_from_command(message: types.Message, start_index: int) -> str:
    if len(message.command) <= start_index:
        return DEFAULT_REASON
    reason = " ".join(message.command[start_index:]).strip()
    return reason[:MAX_REASON_LEN] if reason else DEFAULT_REASON


def _is_command_message(message: types.Message) -> bool:
    text = message.text or message.caption or ""
    return text.startswith("/")


def _format_user_link(user_id: int, name: str | None = None) -> str:
    label = html_escape(name or str(user_id))
    return f'<a href="tg://user?id={user_id}">{label}</a>'


def _format_dt(value) -> str:
    if not value:
        return "Unknown"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M UTC")
    return html_escape(str(value))


def _looks_like_chat_target(raw: str) -> bool:
    lowered = raw.lower()
    return (
        lowered in {"here", "this", "current"}
        or raw.startswith("@")
        or raw.lstrip("-").isdigit()
    )


async def _resolve_user_target(message: types.Message, *, allow_reply: bool = True):
    if allow_reply and message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.first_name, 1

    if len(message.command) < 2:
        raise ValueError("Usage: <code>/gban user_id|@username|reply [reason]</code>")

    raw = message.command[1]
    if raw.lstrip("-").isdigit():
        user_id = int(raw)
        if user_id <= 0:
            raise ValueError("Provide a valid user ID, not a group/chat ID.")
        user_name = None
        try:
            user = await app.get_users(user_id)
            user_name = user.first_name
        except Exception:
            pass
        return user_id, user_name, 2

    try:
        user = await app.get_users(raw)
    except Exception as exc:
        raise ValueError("Could not resolve that user. Use a numeric user ID or reply to their message.") from exc

    return user.id, user.first_name, 2


async def _resolve_group_target(message: types.Message, *, require_target: bool = False):
    current_chat_is_group = message.chat and message.chat.type in GROUP_CHAT_TYPES
    has_arg = len(message.command) > 1

    if current_chat_is_group and not require_target and (
        not has_arg or (not require_target and not _looks_like_chat_target(message.command[1]))
    ):
        return message.chat.id, message.chat.title, 1

    if not has_arg:
        raise ValueError("Usage: <code>/gbangroup chat_id|@chat|here [reason]</code>")

    raw = message.command[1]
    if raw.lower() in {"here", "this", "current"}:
        if not current_chat_is_group:
            raise ValueError("Use this shortcut from the group you want to target.")
        return message.chat.id, message.chat.title, 2

    if raw.lstrip("-").isdigit():
        chat_id = int(raw)
        if chat_id > 0:
            raise ValueError("Provide a group/supergroup/channel ID, not a private user ID.")
        chat_title = None
        try:
            chat = await app.get_chat(chat_id)
            chat_title = chat.title or chat.username
        except Exception:
            pass
        return chat_id, chat_title, 2

    try:
        chat = await app.get_chat(raw)
    except Exception as exc:
        raise ValueError("Could not resolve that chat. Use a numeric chat ID or @publicchat.") from exc

    if chat.type in PRIVATE_CHAT_TYPES:
        raise ValueError("That target is a private chat, not a group.")
    return chat.id, chat.title or chat.username, 2


async def _reply_banned_user(message: types.Message, ban_doc: dict):
    if message.chat.type not in PRIVATE_CHAT_TYPES and not _is_command_message(message):
        return
    reason = html_escape(ban_doc.get("reason") or DEFAULT_REASON)
    await message.reply_text(
        "<b>You are globally banned from using this bot.</b>\n"
        f"<b>Reason:</b> {reason}",
        parse_mode=enums.ParseMode.HTML,
    )


async def _leave_banned_chat(client, chat_id: int, *, reason: str | None = None):
    client_name = getattr(client, "name", "bot")
    cache_key = (client_name, chat_id)
    if cache_key not in _notified_banned_chats:
        _notified_banned_chats.add(cache_key)
        text = "<b>This chat is globally banned. Leaving now.</b>"
        if reason:
            text += f"\n<b>Reason:</b> {html_escape(reason)}"
        try:
            if hasattr(client, "send_message_safe"):
                await client.send_message_safe(chat_id, text, parse_mode=enums.ParseMode.HTML)
            else:
                await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
    try:
        await client.leave_chat(chat_id)
    except (errors.Forbidden, errors.Unauthorized, errors.PeerIdInvalid, errors.ChannelInvalid):
        pass
    except Exception as exc:
        LOGGER.warning("Failed to leave gbanned chat %s with %s: %s", chat_id, client_name, exc)


async def _message_is_blocked(client, message: types.Message) -> bool:
    try:
        if message.chat and message.chat.type in GROUP_CHAT_TYPES:
            group_ban = await get_group_gban(message.chat.id)
            if group_ban:
                await _leave_banned_chat(client, message.chat.id, reason=group_ban.get("reason"))
                return True

        user = message.from_user
        if user and not _is_privileged(user.id):
            user_ban = await get_user_gban(user.id)
            if user_ban:
                await _reply_banned_user(message, user_ban)
                return True
    except Exception as exc:
        LOGGER.error("Global ban message guard failed open: %s", exc, exc_info=True)

    return False


async def _callback_is_blocked(client, query: types.CallbackQuery) -> bool:
    try:
        chat = query.message.chat if query.message else None
        if chat and chat.type in GROUP_CHAT_TYPES:
            group_ban = await get_group_gban(chat.id)
            if group_ban:
                try:
                    await query.answer("This chat is globally banned.", show_alert=True)
                except Exception:
                    pass
                await _leave_banned_chat(client, chat.id, reason=group_ban.get("reason"))
                return True

        user = query.from_user
        if user and not _is_privileged(user.id):
            user_ban = await get_user_gban(user.id)
            if user_ban:
                try:
                    await query.answer("You are globally banned from using this bot.", show_alert=True)
                except Exception:
                    pass
                return True
    except Exception as exc:
        LOGGER.error("Global ban callback guard failed open: %s", exc, exc_info=True)

    return False


async def _gban_message_guard(client, message: types.Message):
    if await _message_is_blocked(client, message):
        raise StopPropagation
    raise ContinuePropagation


async def _gban_callback_guard(client, query: types.CallbackQuery):
    if await _callback_is_blocked(client, query):
        raise StopPropagation
    raise ContinuePropagation


@app.on_message(~filters.bot, group=-30)
async def app_gban_message_guard(client, message: types.Message):
    await _gban_message_guard(client, message)


@game_bot.on_message(~filters.bot, group=-30)
async def game_bot_gban_message_guard(client, message: types.Message):
    await _gban_message_guard(client, message)


@app.on_callback_query(group=-30)
async def app_gban_callback_guard(client, query: types.CallbackQuery):
    await _gban_callback_guard(client, query)


@game_bot.on_callback_query(group=-30)
async def game_bot_gban_callback_guard(client, query: types.CallbackQuery):
    await _gban_callback_guard(client, query)


@app.on_message(filters.command("gban") & sudo_filter)
@handle_errors
async def gban_user_handler(_, message: types.Message):
    try:
        target_id, target_name, reason_index = await _resolve_user_target(message)
    except ValueError as exc:
        return await message.reply_text(str(exc), parse_mode=enums.ParseMode.HTML)

    if _is_privileged(target_id):
        return await message.reply_text("You cannot globally ban the owner or a sudo user.")

    reason = _reason_from_command(message, reason_index)
    previous = await get_user_gban(target_id)
    ban_doc = await add_user_gban(
        target_id,
        reason=reason,
        banned_by=message.from_user.id,
        user_name=target_name,
    )

    action = "Updated global ban" if previous else "Globally banned user"
    await message.reply_text(
        f"<b>{action}</b>\n"
        f"<b>User:</b> {_format_user_link(target_id, target_name)} (<code>{target_id}</code>)\n"
        f"<b>Reason:</b> {html_escape(reason)}\n"
        f"<b>Expires:</b> {_format_dt(ban_doc.get('expires_at_dt'))}",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command("ungban") & sudo_filter)
@handle_errors
async def ungban_user_handler(_, message: types.Message):
    try:
        target_id, target_name, _ = await _resolve_user_target(message)
    except ValueError as exc:
        return await message.reply_text("Usage: <code>/ungban user_id|@username|reply</code>", parse_mode=enums.ParseMode.HTML)

    removed = await remove_user_gban(target_id)
    if not removed:
        return await message.reply_text("That user is not globally banned.")

    await message.reply_text(
        f"<b>Removed global user ban</b>\n"
        f"<b>User:</b> {_format_user_link(target_id, target_name)} (<code>{target_id}</code>)",
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command(["gbangroup", "gchatban"]) & sudo_filter)
@handle_errors
async def gban_group_handler(_, message: types.Message):
    try:
        chat_id, chat_title, reason_index = await _resolve_group_target(message)
    except ValueError as exc:
        return await message.reply_text(str(exc), parse_mode=enums.ParseMode.HTML)

    reason = _reason_from_command(message, reason_index)
    previous = await get_group_gban(chat_id)
    ban_doc = await add_group_gban(
        chat_id,
        reason=reason,
        banned_by=message.from_user.id,
        chat_title=chat_title,
    )
    await group_collection.delete_one({"group_id": chat_id})

    action = "Updated global group ban" if previous else "Globally banned group"
    await message.reply_text(
        f"<b>{action}</b>\n"
        f"<b>Chat:</b> {html_escape(chat_title or str(chat_id))} (<code>{chat_id}</code>)\n"
        f"<b>Reason:</b> {html_escape(reason)}\n"
        f"<b>Expires:</b> {_format_dt(ban_doc.get('expires_at_dt'))}",
        parse_mode=enums.ParseMode.HTML,
    )

    await _leave_banned_chat(app, chat_id, reason=reason)
    await _leave_banned_chat(game_bot, chat_id, reason=reason)


@app.on_message(filters.command(["ungbangroup", "ungchatban"]) & sudo_filter)
@handle_errors
async def ungban_group_handler(_, message: types.Message):
    try:
        chat_id, chat_title, _ = await _resolve_group_target(message, require_target=True)
    except ValueError as exc:
        return await message.reply_text("Usage: <code>/ungbangroup chat_id|@chat|here</code>", parse_mode=enums.ParseMode.HTML)

    removed = await remove_group_gban(chat_id)
    if not removed:
        return await message.reply_text("That chat is not globally banned.")

    await message.reply_text(
        f"<b>Removed global group ban</b>\n"
        f"<b>Chat:</b> {html_escape(chat_title or str(chat_id))} (<code>{chat_id}</code>)",
        parse_mode=enums.ParseMode.HTML,
    )


def _format_user_ban_line(doc: dict) -> str:
    user_id = doc.get("user_id")
    name = html_escape(doc.get("user_name") or "Unknown")
    reason = html_escape(doc.get("reason") or DEFAULT_REASON)
    expires = _format_dt(doc.get("expires_at_dt"))
    return f"- <code>{user_id}</code> | {name} | expires {expires} | {reason}"


def _format_group_ban_line(doc: dict) -> str:
    chat_id = doc.get("chat_id")
    title = html_escape(doc.get("chat_title") or "Unknown")
    reason = html_escape(doc.get("reason") or DEFAULT_REASON)
    expires = _format_dt(doc.get("expires_at_dt"))
    return f"- <code>{chat_id}</code> | {title} | expires {expires} | {reason}"


@app.on_message(filters.command("gbanlist") & sudo_filter)
@handle_errors
async def gban_list_handler(_, message: types.Message):
    scope = message.command[1].lower() if len(message.command) > 1 else "all"
    show_users = scope in {"all", "users", "user", "u"}
    show_groups = scope in {"all", "groups", "group", "chats", "chat", "g"}

    if not show_users and not show_groups:
        return await message.reply_text("Usage: <code>/gbanlist [users|groups]</code>", parse_mode=enums.ParseMode.HTML)

    sections = []
    active_filter = {
        "$or": [
            {"expires_at_dt": {"$exists": False}},
            {"expires_at_dt": {"$gt": get_now_utc()}},
        ]
    }
    if show_users:
        user_count = await global_user_bans_collection.count_documents(active_filter)
        user_docs = await global_user_bans_collection.find(active_filter, {"_id": 0}).sort("created_at", -1).limit(20).to_list(length=20)
        lines = [_format_user_ban_line(doc) for doc in user_docs] or ["No globally banned users."]
        sections.append(f"<b>Users:</b> <code>{user_count}</code>\n" + "\n".join(lines))

    if show_groups:
        group_count = await global_group_bans_collection.count_documents(active_filter)
        group_docs = await global_group_bans_collection.find(active_filter, {"_id": 0}).sort("created_at", -1).limit(20).to_list(length=20)
        lines = [_format_group_ban_line(doc) for doc in group_docs] or ["No globally banned groups."]
        sections.append(f"<b>Groups:</b> <code>{group_count}</code>\n" + "\n".join(lines))

    await message.reply_text(
        "<b>Global Ban List</b>\n\n" + "\n\n".join(sections),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_message(filters.command(["gbanstatus", "gbaninfo"]) & sudo_filter)
@handle_errors
async def gban_status_handler(_, message: types.Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: <code>/gbanstatus user_id|chat_id</code>", parse_mode=enums.ParseMode.HTML)

    if message.reply_to_message and message.reply_to_message.from_user and len(message.command) < 2:
        target_id = message.reply_to_message.from_user.id
    else:
        raw = message.command[1]
        if not raw.lstrip("-").isdigit():
            return await message.reply_text("Use a numeric user ID or chat ID for status checks.")
        target_id = int(raw)

    if target_id < 0:
        doc = await get_group_gban(target_id)
        if not doc:
            return await message.reply_text("That chat is not globally banned.")
        await message.reply_text(
            "<b>Global Group Ban</b>\n"
            f"<b>Chat:</b> {html_escape(doc.get('chat_title') or str(target_id))} (<code>{target_id}</code>)\n"
            f"<b>Reason:</b> {html_escape(doc.get('reason') or DEFAULT_REASON)}\n"
            f"<b>Banned by:</b> <code>{doc.get('banned_by')}</code>\n"
            f"<b>Date:</b> {_format_dt(doc.get('created_at'))}\n"
            f"<b>Expires:</b> {_format_dt(doc.get('expires_at_dt'))}",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    doc = await get_user_gban(target_id)
    if not doc:
        return await message.reply_text("That user is not globally banned.")

    await message.reply_text(
        "<b>Global User Ban</b>\n"
        f"<b>User:</b> {_format_user_link(target_id, doc.get('user_name'))} (<code>{target_id}</code>)\n"
        f"<b>Reason:</b> {html_escape(doc.get('reason') or DEFAULT_REASON)}\n"
        f"<b>Banned by:</b> <code>{doc.get('banned_by')}</code>\n"
        f"<b>Date:</b> {_format_dt(doc.get('created_at'))}\n"
        f"<b>Expires:</b> {_format_dt(doc.get('expires_at_dt'))}",
        parse_mode=enums.ParseMode.HTML,
    )
