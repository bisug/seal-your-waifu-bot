import os

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    # --- BOT IDENTITY ---
    TOKEN = os.getenv("TOKEN", "7888451649:AAFsl_vtOiN7dDvE-bLx32WJ-Gof-oc1zA0")
    SUB_TOKEN = os.getenv("SUB_TOKEN", "8785400009:AAG6gvkM-BH8Jq7NCKzVczNRUPrkm3O9-Y4")
    BOT_USERNAME = None  # Fetched automatically at startup
    BOT_ID = None        # Fetched automatically at startup
    BOT_NAME = None      # Fetched automatically at startup

    # --- TELEGRAM API CREDENTIALS ---
    API_ID = int(os.getenv("API_ID", "25635673"))
    API_HASH = os.getenv("API_HASH", "ec69ce8b56c71541499c914fabd08286")

    # --- DATABASE INFRASTRUCTURE ---
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    REDIS_URL = os.getenv("REDIS_URL", "redis://:UvSaz52wKSnIJfapNAaVkF7apl0xKwh2@redis-13252.crce283.ap-south-1-2.ec2.cloud.redislabs.com:13252")

    # --- PRIVILEGED USERS ---
    OWNER_ID = int(os.getenv("OWNER_ID", "7804972365"))
    SUDO_USERS = [int(i.strip()) for i in os.getenv("SUDO_USERS", "7717913705, 6574393060, 6388703157, 6858372924").split(",") if i.strip().isdigit()]

    # --- CHANNEL & GROUP IDS ---
    MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID", "-1002429397912"))
    GALLERY_CHANNEL_ID = int(os.getenv("GALLERY_CHANNEL_ID", "-1003925872981"))
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1002913644675"))
    
    # --- SOCIAL & CHATS ---
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "TNJBotSupport")
    UPDATE_CHAT = os.getenv("UPDATE_CHAT", "SEAL_UPDATE")
    
    # --- MEDIA & ASSETS ---
    PHOTO_URL = os.getenv("PHOTO_URL", "https://files.catbox.moe/2hsawz.jpg").split(",")

    # --- EXTERNAL INTEGRATIONS ---
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "21786e21eb0369339a3c2a2d9c561190")
    
    # --- WEBAPP CONFIG ---
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://dear-project-seal-64ed7a272fd6.herokuapp.com")
    MINI_APP_SHORT_NAME = os.getenv("MINI_APP_SHORT_NAME", "app") # The 'Short Name' you set in BotFather
    API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "v1_7b82")

    # --- USERBOT CONFIG ---
    STRING_SESSION = os.getenv("STRING_SESSION", "BQEyrwMApp5yi6-jKRCfwSBL2tVRNfSgDCGYMh61lWDKQnYwkDIQc6xaKuavcM_jCv0RYUEq1ye_hwpx5Mw-jRlDLGROn8eZ3RFQniaMALDiGnwsRWD82ReJsXV-zPsFlcf7nT60bis0bALIBAbKeR8gBcnba5q9tgmWXd11sSRmvQy9zgXJ7K8PM4Zvi_9sCOSuyQhd6R_NicLWTW3dIMUbwznCrWi8-FZA21kxD3YfitVEHyR_C4LUhkYPlP8iqkQzrxbIDwVZ8Zr-3gsw38u40PT1RqqjDyhIr8wl1KX4Pt3QUqAAttyiq5e5BaT2WLc7ga4Sxb_NwJqBKlNU0vRUnYHxegAAAAHXQT_PAA")

config = Config()
