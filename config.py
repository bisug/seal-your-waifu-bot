import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    # Bot identity
    TOKEN = os.getenv("TOKEN", "7888451649:AAGqpCops8LxBCs54h23SmD771TKRMucGh8")
    SUB_TOKEN = os.getenv("SUB_TOKEN", "7888451649:AAGqpCops8LxBCs54h23SmD771TKRMucGh8") # Placeholder, user should update this
    BOT_USERNAME = None  # Fetched automatically at startup

    # Telegram API credentials
    API_ID = int(os.getenv("API_ID", "25635673"))
    API_HASH = os.getenv("API_HASH", "ec69ce8b56c71541499c914fabd08286")

    # Database
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    REDIS_URL = os.getenv("REDIS_URL", "rediss://default:AY_bAAIncDEwNWNkODM3NjgxN2M0Y2ZhODZlMDAzYTI4MzY2M2U1M3AxMzY4Mjc@civil-monster-36827.upstash.io:6379")

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
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "21786e21eb0369339a3c2a2d9c561190")
    EXTOL_API_KEY = os.getenv("EXTOL_API_KEY", "IAC-49ZENKUeYt")
    EXTOL_RECEIVER = os.getenv("EXTOL_RECEIVER", "EXTAF9VYPP67bpFWJmw301503c4")

    # WebApp
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://dear-project-01-seal-6d4f0ddd98e4.herokuapp.com")

    # Batch Processing
    BATCH_MONGO_URI = os.getenv("BATCH_MONGO_URI", "mongodb+srv://riyu:riyu@cluster0.kduyo99.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    BATCH_STRING_SESSION = os.getenv("BATCH_STRING_SESSION", "BQGrPU8AXHUix6jIMWTz9xp5ZT7MZcozFawIKPIWgy63stW3UYp77MXSHmfLTHmpqXycrCCJqXYE7qj6fU5wZK7MVyqFUFogETZX7Qfzk8s7z_zUXMNVomTnYImRVQ0jR5T8UWattvz3mFFu0l5M5QhPWxabk7N2DTu5ZGgJ8ZWIfXZL_A1ZjGmiT_BZOlrvG5meVMpOuc_Sti3MPp6hYOpXA-tBwVAMh075Ty1yVyoCx61ODmbi6PYPBjcDF0r3KihyGsnaPJg8mgeYgca6WvpqwdsQDud2xUD1TRn6RqqTeC575kZZNn2CERd-35brznfH5Yy1rmVpe-fXT_m-maWB8nGypQAAAAFtzc3-AA")

config = Config()
