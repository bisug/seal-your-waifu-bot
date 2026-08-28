import os

from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default

class Config:
    # SECURITY: no secret defaults here. Credentials live in backend/.env
    # (git-ignored, local dev) and platform env vars (production). The old
    # hardcoded defaults were committed to git history and must be rotated.
    # --- BOT IDENTITY ---
    TOKEN = os.getenv("TOKEN", "")
    SUB_TOKEN = os.getenv("SUB_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "SealYourWaifuBot")  # Fetched automatically at startup
    BOT_ID = None        # Fetched automatically at startup
    BOT_NAME = os.getenv("BOT_NAME", "SEAL YOUR WAIFU")  # Fetched automatically at startup

    # --- TELEGRAM API CREDENTIALS ---
    API_ID = int(os.getenv("API_ID", "0") or 0)
    API_HASH = os.getenv("API_HASH", "")

    # --- DATABASE INFRASTRUCTURE ---
    MONGO_URL = os.getenv("MONGO_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "")

    # --- PRIVILEGED USERS ---
    OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
    SUDO_USERS = [int(i.strip()) for i in os.getenv("SUDO_USERS", "").split(",") if i.strip().isdigit()]

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
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")
    
    # --- WEBAPP CONFIG ---
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://example.com")
    MINI_APP_SHORT_NAME = os.getenv("MINI_APP_SHORT_NAME", "app") # The 'Short Name' you set in BotFather
    API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "v1_7b82")

    # --- LOGGING ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # text or json
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "seal-bot.log")
    LOG_FILE_ENABLED = _env_bool("LOG_FILE_ENABLED", False)
    LOG_MAX_BYTES = _env_int("LOG_MAX_BYTES", 10 * 1024 * 1024)
    LOG_BACKUP_COUNT = _env_int("LOG_BACKUP_COUNT", 5)
    LOG_UTC = _env_bool("LOG_UTC", True)

    # --- RESOURCE MANAGEMENT ---
    RESOURCE_MONITOR_ENABLED = _env_bool("RESOURCE_MONITOR_ENABLED", True)
    RESOURCE_CHECK_INTERVAL_SECONDS = _env_float("RESOURCE_CHECK_INTERVAL_SECONDS", 60.0)
    RESOURCE_MEMORY_SOFT_LIMIT_MB = _env_int("RESOURCE_MEMORY_SOFT_LIMIT_MB", 0)  # 0 = auto
    RESOURCE_MEMORY_HARD_LIMIT_MB = _env_int("RESOURCE_MEMORY_HARD_LIMIT_MB", 0)  # 0 = auto
    RESOURCE_MIN_AVAILABLE_MB = _env_int("RESOURCE_MIN_AVAILABLE_MB", 0)  # 0 = auto
    RESOURCE_GC_COOLDOWN_SECONDS = _env_float("RESOURCE_GC_COOLDOWN_SECONDS", 120.0)
    RESOURCE_TASK_SOFT_LIMIT = _env_int("RESOURCE_TASK_SOFT_LIMIT", 500)
    RESOURCE_SHUTDOWN_TIMEOUT_SECONDS = _env_float("RESOURCE_SHUTDOWN_TIMEOUT_SECONDS", 10.0)
    RESOURCE_REDIS_PURGE_BATCH_SIZE = _env_int("RESOURCE_REDIS_PURGE_BATCH_SIZE", 100)
    REDIS_MEMORY_LIMIT_MB = _env_int("REDIS_MEMORY_LIMIT_MB", 0)  # 0 = auto from Redis maxmemory

    # --- USERBOT CONFIG ---
    STRING_SESSION = os.getenv("STRING_SESSION", "")

config = Config()
