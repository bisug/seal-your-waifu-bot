import re
import html

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

async def check_member_requirement(chat, min_count=50):
    """
    Checks if a chat meets the minimum member requirement for GameBot.
    Returns (bool, current_count).
    """
    from pyrogram import enums
    if chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        return True, 0
        
    try:
        count = await chat.get_members_count()
        return count >= min_count, count
    except Exception:
        # If we can't check (e.g., bot not in group), assume True to avoid blocking if the bot just joined
        return True, 0
