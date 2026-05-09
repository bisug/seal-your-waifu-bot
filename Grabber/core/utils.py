import asyncio
import html
import logging
import re
from datetime import datetime, timezone
from functools import wraps
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

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
def md_escape(text: str) -> str:
    """Escapes special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    # Characters to escape in MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)
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
        return True, None, 0
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

def handle_errors(func):
    """
    Decorator to handle common Pyrogram errors in command handlers.
    Catches FloodWait, SlowmodeWait, and other API errors.
    """
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except errors.FloodWait as e:
            LOGGER.warning(f"FloodWait in {func.__name__}: {e.value}s")
            await asyncio.sleep(e.value)
            try:
                return await func(client, message, *args, **kwargs)
            except Exception as e2:
                LOGGER.error(f"Retry after FloodWait failed in {func.__name__}: {e2}")
        except errors.SlowmodeWait as e:
            LOGGER.warning(f"SlowmodeWait in {func.__name__}: {e.value}s")
            # Usually we don't sleep for slowmode in a handler, just inform or ignore
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"Permission error in {func.__name__}: {e}")
        except errors.MessageNotModified:
            pass
        except errors.BadRequest as e:
            LOGGER.error(f"BadRequest in {func.__name__}: {e}")
        except Exception as e:
            LOGGER.error(f"Unhandled error in {func.__name__}: {e}", exc_info=True)
    return wrapper
