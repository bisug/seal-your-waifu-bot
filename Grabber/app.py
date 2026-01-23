from pyrogram import Client
from config import config

# Constants for ease of access
api_id = config.API_ID
api_hash = config.API_HASH
bot_token = config.TOKEN

# Initialize the shared Client instance
app = Client(
    name="Grabber",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)

# Set global prefix for command filters (Strictly '/')
from pyrogram import filters

_original_command = filters.command

def patched_command(commands, prefixes="/", case_sensitive=False):
    return _original_command(commands, prefixes, case_sensitive)

filters.command = patched_command

