import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    # --- BOT IDENTITY ---
    TOKEN = os.getenv("TOKEN")
    SUB_TOKEN = os.getenv("SUB_TOKEN")
    BOT_USERNAME = None  # Fetched automatically at startup
    BOT_ID = None        # Fetched automatically at startup
    BOT_NAME = None      # Fetched automatically at startup

    # --- TELEGRAM API CREDENTIALS ---
    API_ID = int(os.getenv("API_ID") or 0)
    API_HASH = os.getenv("API_HASH")

    # ==========================================
    # ---      DATABASE INFRASTRUCTURE     ---
    # ==========================================
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://botmaker9675208:botmaker9675208@cluster0.sc9mq8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    REDIS_URL = os.getenv("REDIS_URL", "rediss://default:AVNS_3H0cohKfeMSPJAn2TeO@sealbot-friendclub-35f1.k.aivencloud.com:28970")

    # --- PRIVILEGED USERS ---
    OWNER_ID = int(os.getenv("OWNER_ID") or 0)
    SUDO_USERS = [int(i.strip()) for i in os.getenv("SUDO_USERS", "7717913705, 6574393060, 6388703157, 6858372924").split(",") if i.strip().isdigit()]

    # ==========================================
    # ---       CHANNEL & GROUP IDS        ---
    # ==========================================
    MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID") or -1002429397912)
    GALLERY_CHANNEL_ID = int(os.getenv("GALLERY_CHANNEL_ID") or -1003925872981)
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID") or -1002913644675)
    
    # ==========================================
    # ---          SOCIAL & CHATS          ---
    # ==========================================
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "TNJBotSupport")
    UPDATE_CHAT = os.getenv("UPDATE_CHAT", "SEAL_UPDATE")
    
    # ==========================================
    # ---          MEDIA & ASSETS          ---
    # ==========================================
    PHOTO_URL = os.getenv("PHOTO_URL", "https://files.catbox.moe/2hsawz.jpg").split(",")

    # ==========================================
    # ---       EXTERNAL INTEGRATIONS      ---
    # ==========================================
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "21786e21eb0369339a3c2a2d9c561190")
    
    # ==========================================
    # ---           WEBAPP CONFIG          ---
    # ==========================================
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://dear-project-seal-64ed7a272fd6.herokuapp.com")
    MINI_APP_SHORT_NAME = os.getenv("MINI_APP_SHORT_NAME", "app")
    API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "v1_7b82")

    # ==========================================
    # ---           USERBOT CONFIG         ---
    # ==========================================
    STRING_SESSION = os.getenv("STRING_SESSION")

config = Config()
