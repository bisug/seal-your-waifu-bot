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
    bot_token=bot_token,
    plugins=dict(root="Grabber/modules") # This enables automatic plugin loading if wanted, but we use explicit imports in __main__
)
