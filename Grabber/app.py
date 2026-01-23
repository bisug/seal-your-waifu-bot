from pyrogram import Client, filters
from config import config

# Monkeypatch filters.command to enforce '/' globally before any modules are loaded
_original_command = filters.command

def patched_command(commands, prefixes="/", case_sensitive=False):
    """Global prefix enforcement for all command filters."""
    return _original_command(commands, prefixes, case_sensitive)

filters.command = patched_command

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
