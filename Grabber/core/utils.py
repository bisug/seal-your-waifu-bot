import re

def md_escape(text: str) -> str:
    """Escapes markdown-sensitive characters in a string."""
    if not text:
        return ""
    # Characters that need escaping in Pyrogram's Markdown implementation
    # We escape: * _ ` [ ]
    # pyre-ignore
    return re.sub(r"([\*_`\[\]])", r"\\\1", text)
