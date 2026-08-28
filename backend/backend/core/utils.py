import asyncio
import html
import logging
from datetime import datetime, timezone
from functools import wraps
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from backend.core.constants import PERMISSION_DENIED_ERRORS
from backend.database import r as _redis

def get_now_utc() -> datetime:
    """Returns the current aware UTC datetime."""
    return datetime.now(timezone.utc)
LOGGER = logging.getLogger(__name__)
def normalize_user_id(uid):
    """
    Normalizes a user ID that might be stored as an int, string, or 
    a single-item list. Returns the ID as an integer.
    """
    if isinstance(uid, list):
        if not uid: return 0
        uid = uid[0]
    try:
        return int(uid)
    except (ValueError, TypeError):
        return 0
def get_user_id_query(user_id):
    """
    Returns a MongoDB query mapping for user IDs, resolving type inconsistencies
    between integers and strings stored dynamically in MongoDB collections.
    """
    uid_int = normalize_user_id(user_id)
    return {"id": {"$in": [uid_int, str(uid_int)]}}
def html_escape(text: str) -> str:
    """Escapes special characters for Telegram HTML."""
    if not text:
        return ""
    return html.escape(text, quote=False)
def format_currency(amount: int, symbol: str = "⬪") -> str:
    """Formats an integer amount with commas and appends a symbol."""
    try:
        if not amount: return f"0 {symbol}"
        return f"{int(amount):,} {symbol}"
    except (ValueError, TypeError):
        return f"0 {symbol}"
async def check_member_requirement(bot, chat, min_count=50):
    """
    Checks if a chat meets the requirements for GameBot:
    1. Minimum 50 members.
    2. Main Bot (BOT_ID) is present in the group.
    Returns (bool, str_reason, current_count).
    """
    from pyrogram import enums, errors, filters, types
    from config import config
    if chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        return False, "group_only", 0
    try:
        # 1. Check member count
        # In Pyrogram V2, get_chat_members_count is on the Client, not the Chat object.
        count = await bot.get_chat_members_count(chat.id)
        if count < min_count:
            return False, "member_count", count
        # 2. Check Main Bot presence
        try:
            # We check if BOT_ID (Main Bot) is in this chat
            await bot.get_chat_member(chat.id, config.BOT_ID)
        except errors.UserNotParticipant:
            return False, "main_bot_missing", count
        except Exception as e:
            LOGGER.debug(f"User participation check failed: {e}")
            pass
        return True, None, count
    except Exception as e:
        LOGGER.error(f"Group membership resolution error: {e}")
        return False, "membership_check_failed", 0
async def send_media_dynamic(client, chat_id, media_url, **kwargs):
    """Dynamically sends either a photo or a video based on the URL extension."""
    from pyrogram import enums, errors, filters, types
    if isinstance(media_url, str) and media_url.endswith(('.mp4', '.webm', '.gif')):
        return await client.send_video(chat_id, video=media_url, **kwargs)
    return await client.send_photo(chat_id, photo=media_url, **kwargs)
async def reply_media_dynamic(message_obj, media_url, **kwargs):
    """Dynamically replies with either a photo or a video based on the URL extension."""
    if isinstance(media_url, str) and media_url.endswith(('.mp4', '.webm', '.gif')):
        return await message_obj.reply_video(video=media_url, **kwargs)
    return await message_obj.reply_photo(photo=media_url, **kwargs)

async def notify_handler_error(update, text: str = "This command failed. Please try again."):
    """Best-effort user-visible notice for command/callback failures."""
    try:
        if isinstance(update, types.CallbackQuery):
            await update.answer(text, show_alert=True)
        elif hasattr(update, "reply_text"):
            await update.reply_text(f"<b>{html_escape(text)}</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.debug(f"Could not send handler error notice: {e}")

def handle_errors(func):
    """
    Decorator to handle common Pyrogram errors in command handlers,
    and enforce that users must start the bot in DM first.
    """
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        from backend.core.user import get_cached_user
        from backend.database import user_collection
        from config import config

        # 0. Idempotency: dedupe by (chat_id, message_id) to collapse
        # reconnect/replay re-deliveries of the same update. Skips silent on
        # any error or when Redis is unavailable (failsafe: allow).
        try:
            _src = message if isinstance(message, types.Message) else getattr(message, "message", None)
            if _src is not None and _src.chat is not None and _redis is not None:
                _dedup_key = f"dedup:{_src.chat.id}:{_src.id}"
                if not await _redis.set(_dedup_key, "1", ex=60, nx=True):
                    return
        except Exception:
            pass

        # 1. Registration Check
        user = getattr(message, "from_user", None)
        if user:
            from backend.core.roles import is_staff

            is_sudo = is_staff(user.id)

            is_start = False
            if isinstance(message, types.Message):
                text = message.text or message.caption or ""
                if text.startswith("/start"):
                    is_start = True
            elif isinstance(message, types.CallbackQuery):
                if message.data and message.data.startswith(("st:", "help:", "free_spin")):
                    is_start = True

            if not is_start and not is_sudo:
                cached = await get_cached_user(user.id)
                if not cached:
                    db_user = await user_collection.find_one({"id": {"$in": [user.id, str(user.id)]}})
                    if not db_user:
                        markup = types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton("🚀 Start Bot in DM", url=f"https://t.me/{config.BOT_USERNAME}?start=true")
                        ]])
                        text = f"❌ <b>Access Denied</b>\n\n<a href='tg://user?id={user.id}'>{html_escape(user.first_name)}</a>, you must start the bot in private messages first before playing!"
                        if hasattr(message, "reply_text"):
                            try:
                                await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                            except Exception:
                                pass
                        elif hasattr(message, "answer"):
                            try:
                                await message.answer("You must start the bot in PM first!", show_alert=True)
                            except Exception:
                                pass
                        return # Stop execution!

        # 2. Proceed with handler inside try-except
        try:
            return await func(client, message, *args, **kwargs)
        except FloodWait as e:
            LOGGER.warning(f"FloodWait in {func.__name__}: {e.value}s")
            await asyncio.sleep(e.value)
            try:
                return await func(client, message, *args, **kwargs)
            except Exception as e2:
                LOGGER.error(f"Retry after FloodWait failed in {func.__name__}: {e2}", exc_info=True)
                await notify_handler_error(message)
        except errors.SlowmodeWait as e:
            LOGGER.warning(f"SlowmodeWait in {func.__name__}: {e.value}s")
            await notify_handler_error(message, f"Slowmode is active. Try again in {e.value}s.")
        except PERMISSION_DENIED_ERRORS as e:
            LOGGER.debug(f"Permission error in {func.__name__}: {e}")
        except errors.MessageNotModified:
            pass
        except errors.BadRequest as e:
            LOGGER.error(f"BadRequest in {func.__name__}: {e}", exc_info=True)
            await notify_handler_error(message)
        except Exception as e:
            LOGGER.error(f"Unhandled error in {func.__name__}: {e}", exc_info=True)
            await notify_handler_error(message)
    return wrapper
