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
