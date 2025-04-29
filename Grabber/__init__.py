import logging  
from pyrogram import Client 

from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

OWNER_ID = '6574393060'
sudo_users = ["7717913705"]
GROUP_ID = "-1002528887253"
SUPPORT_ID = "-1002528887253"
TOKEN = ""
mongo_url = "REDACTED_MONGO_URI"
PHOTO_URL = ["https://files.catbox.moe/2hsawz.jpg"]
SUPPORT_CHAT = "seal_Your_WH_Group"
UPDATE_CHAT = "SEAL_UPDATE"
BOT_USERNAME = "Seal_Your_Waifu_Bot"
CHARA_CHANNEL_ID = "-1002643258398"
api_id = "25635673"
api_hash = "REDACTED_API_HASH"
JOINLOGS = "-1002036001760"
LEAVELOGS = "-1002036001760"

application = Application.builder().token(TOKEN).build()
Grabberu = Client("Grabber", api_id, api_hash, bot_token=TOKEN)
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catchers']
collection = db['anime_characterss']
group_collection = db['total_groups']
user_totals_collection = db['user_totalssss']
message_counts_collection = db['message']
user_collection = db["user_collectionsss"]
group_user_totals_collection = db['group_user_totals']
top_global_groups_collection = db['top_global_groupss']
