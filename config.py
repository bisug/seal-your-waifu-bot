import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    # Bot identity
    TOKEN =""
    BOT_USERNAME = None  # Fetched automatically at startup
    
    # Telegram API credentials
    API_ID = int(os.getenv("API_ID", "25635673"))
    API_HASH =""
    
    # Database
    MONGO_URL =""
    REDIS_URL =""
    
    # User IDs and Group IDs
    OWNER_ID = int(os.getenv("OWNER_ID", "6574393060"))
    SUDO_USERS = [int(i.strip()) for i in os.getenv("SUDO_USERS", "7717913705, 6574393060, 6388703157, 6858372924").split(",") if i.strip().isdigit()]
    
    GROUP_ID = int(os.getenv("GROUP_ID", "-1002528887253"))
    SUPPORT_ID = int(os.getenv("SUPPORT_ID", "-1002528887253"))
    SUPPORT_GROUP_ID = int(os.getenv("SUPPORT_GROUP_ID", "-1002429397912"))
    CHARA_CHANNEL_ID = int(os.getenv("CHARA_CHANNEL_ID", "-1002643258398"))
    JOINLOGS = int(os.getenv("JOINLOGS", "-1002036001760"))
    LEAVELOGS = int(os.getenv("LEAVELOGS", "-1002036001760"))
    
    # Special IDs for spawns
    SPECIAL_GROUP_ID = int(os.getenv("SPECIAL_GROUP_ID", "-1002528887253"))
    ROYAL_NOTIFY_USER_ID = int(os.getenv("ROYAL_NOTIFY_USER_ID", "7717913705"))
    
    # Chats
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "seal_Your_WH_Group")
    UPDATE_CHAT = os.getenv("UPDATE_CHAT", "SEAL_UPDATE")
    # Media
    PHOTO_URL = os.getenv("PHOTO_URL", "https://files.catbox.moe/2hsawz.jpg").split(",")
    
    # Other APIs
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "REDACTED_API_HASH")
    EXTOL_API_KEY =""
    EXTOL_RECEIVER = os.getenv("EXTOL_RECEIVER", "EXTAF9VYPP67bpFWJmw301503c4")
    
    # Batch Processing
    BATCH_MONGO_URI = os.getenv("BATCH_MONGO_URI", "REDACTED_MONGO_URI")
    BATCH_STRING_SESSION =""

config = Config()
