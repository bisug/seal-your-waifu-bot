import importlib
import re
import time
import logging
import asyncio
from pyrogram import Client, enums, types, filters, errors
from pyrogram.handlers import MessageHandler
from config import config
from Grabber.database import (
    client, db, collection, group_collection,
    user_totals_collection, message_counts_collection,
    user_collection, group_user_totals_collection,
    total_pm_users, sudo_collection,
    spawns_collection, sessions_collection, quiz_questions_collection,
    gamebot_enabled_groups_collection
)

StartTime = time.time()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

OWNER_ID = config.OWNER_ID
sudo_users = config.SUDO_USERS
GROUP_ID = config.GROUP_ID
SUPPORT_ID = config.SUPPORT_ID
SUPPORT_GROUP_ID = config.SUPPORT_GROUP_ID
TOKEN =""
PHOTO_URL = config.PHOTO_URL
SUPPORT_CHAT = config.SUPPORT_CHAT
UPDATE_CHAT = config.UPDATE_CHAT
BOT_USERNAME = config.BOT_USERNAME
GAME_BOT_USERNAME = None
BOT_ID = None
BOT_NAME = None
CHARA_CHANNEL_ID = config.CHARA_CHANNEL_ID
WEB_APP_URL = config.WEB_APP_URL

from Grabber.client import SealClient

app = SealClient(name="MainBot", bot_token=config.TOKEN)
game_bot = SealClient(name="GameBot", bot_token=config.SUB_TOKEN)

# For backward compatibility and modularity
Grabber = app
nguess_bot = game_bot
