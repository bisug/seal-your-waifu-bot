from pyrogram import Client, filters, enums, types
from config import config

# ─── Global ParseMode Enforcer ────────────────────────────────────────────────
# Monkeypatch filters.command to enforce '/' globally before any modules are loaded
_original_command = filters.command

def patched_command(commands, prefixes="/", case_sensitive=False):
    """Global prefix enforcement for all command filters."""
    return _original_command(commands, prefixes, case_sensitive)

filters.command = patched_command

# Monkeypatch Client and Message methods to default parse_mode to MARKDOWN
def wrap_with_default_parsemode(original_method):
    async def wrapped(*args, **kwargs):
        if "parse_mode" not in kwargs:
            kwargs["parse_mode"] = enums.ParseMode.MARKDOWN
        return await original_method(*args, **kwargs)
    return wrapped

# Methods to patch on Client
methods_to_patch = [
    "send_message", "send_photo", "send_video", "send_animation", "send_audio",
    "send_document", "edit_message_text", "edit_message_caption", "edit_message_media"
]

for method_name in methods_to_patch:
    if hasattr(Client, method_name):
        setattr(Client, method_name, wrap_with_default_parsemode(getattr(Client, method_name)))

# Methods to patch on Message
message_methods = [
    "reply_text", "reply_photo", "reply_video", "reply_animation", "reply_audio",
    "reply_document", "edit_text", "edit_caption", "edit_media"
]

for method_name in message_methods:
    if hasattr(types.Message, method_name):
        setattr(types.Message, method_name, wrap_with_default_parsemode(getattr(types.Message, method_name)))

# ──────────────────────────────────────────────────────────────────────────────

# Initialize the shared Client instance
app = Client(
    name="Grabber",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.TOKEN,
    app_version="Seal-Bot v2",
    device_model="Seal-Server",
    system_version="Linux",
    workdir="Grabber"
)
