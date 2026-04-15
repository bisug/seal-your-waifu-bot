import asyncio
import importlib
import logging
import re
import time

from pyrogram import Client, enums, errors, filters, types
from pyrogram.handlers import MessageHandler

from config import config
from Grabber.client import SealClient
from Grabber.database import (client, collection, db,
                              gamebot_enabled_groups_collection,
                              group_collection, group_user_totals_collection,
                              message_counts_collection,
                              scraped_characters_collection, sessions_collection,
                              spawns_collection, sudo_collection,
                              total_pm_users, user_collection,
                              user_totals_collection)

StartTime = time.time()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

OWNER_ID = config.OWNER_ID
sudo_users = config.SUDO_USERS
MAIN_GROUP_ID = config.MAIN_GROUP_ID
TOKEN = config.TOKEN
PHOTO_URL = config.PHOTO_URL
SUPPORT_CHAT = config.SUPPORT_CHAT
UPDATE_CHAT = config.UPDATE_CHAT
BOT_USERNAME = config.BOT_USERNAME
GAME_BOT_USERNAME = None
BOT_ID = None
BOT_NAME = None
GALLERY_CHANNEL_ID = config.GALLERY_CHANNEL_ID
WEB_APP_URL = config.WEB_APP_URL
WEB_APP_URL = config.WEB_APP_URL


app = SealClient(name="MainBot", bot_token=config.TOKEN)
game_bot = SealClient(name="GameBot", bot_token=config.SUB_TOKEN)
userbot = SealClient(name="UserBot", session_string=config.STRING_SESSION) if config.STRING_SESSION else None

# For backward compatibility and modularity
Grabber = app
nguess_bot = game_bot

def _sudo_check(flt, client, message):
    if not message.from_user:
        return False
    return message.from_user.id in sudo_users or message.from_user.id == OWNER_ID

sudo_filter = filters.create(_sudo_check)
