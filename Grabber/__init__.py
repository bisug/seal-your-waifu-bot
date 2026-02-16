import logging
import time
from config import config
from Grabber.app import app
from Grabber.database import (
    client, db, collection, group_collection, 
    user_totals_collection, message_counts_collection, 
    user_collection, group_user_totals_collection, 
    top_global_groups_collection, total_pm_users, sudo_collection,
    spawns_collection, sessions_collection, quiz_questions_collection
)

# Global StartTime
StartTime = time.time()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

# Constants from config for direct access
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
CHARA_CHANNEL_ID = config.CHARA_CHANNEL_ID
JOINLOGS = config.JOINLOGS
LEAVELOGS = config.LEAVELOGS

# For backward compatibility if any module still uses Grabberu
Grabberu = app
