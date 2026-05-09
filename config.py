import os

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    # --- BOT IDENTITY ---
    TOKEN =""
    SUB_TOKEN =""
    BOT_USERNAME = None  # Fetched automatically at startup
    BOT_ID = None        # Fetched automatically at startup
    BOT_NAME = None      # Fetched automatically at startup

    # --- TELEGRAM API CREDENTIALS ---
    API_ID = int(os.getenv("API_ID", "25635673"))
    API_HASH =""

    # --- DATABASE INFRASTRUCTURE ---
    MONGO_URL =""
    REDIS_URL =""

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
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "REDACTED_API_HASH")
    
    # --- WEBAPP CONFIG ---
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://example.com")
    MINI_APP_SHORT_NAME = os.getenv("MINI_APP_SHORT_NAME", "app") # The 'Short Name' you set in BotFather
    API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "v1_7b82")

    # --- USERBOT CONFIG ---
    STRING_SESSION =""

config = Config()
