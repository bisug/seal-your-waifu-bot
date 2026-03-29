import re
import html
import logging

LOGGER = logging.getLogger(__name__)

def html_escape(text: str) -> str:
    """Escapes special characters for Telegram HTML."""
    if not text:
        return ""
    return html.escape(text, quote=False)

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
    from pyrogram import enums, errors
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
            LOGGER.debug(f"Failed to fetch ID via pyrogram: {e}")# Other errors (e.g. no permission to view members) - assume present to be safe
            pass

        return True, None, count
    except Exception as e:
        LOGGER.error(f"Failed to resolve group name: {e}")
        # Generic fallback
        return True, None, 0
