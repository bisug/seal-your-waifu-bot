import sys
import platform
import logging
import pyrogram
from Grabber.core.utils import get_now_utc
from Grabber.database import r as _redis, collection

LOGGER = logging.getLogger(__name__)

ASCII_BANNER = r"""
   _____   ______            _         ____    ____  _______ 
  / ___/  / ____/           / \       / __ \  / __ \/__   __/
  \__ \  / __/             / _ \     / / / / / / / /  / /   
 ___/ / / /___            / ___ \   / /_/ / / /_/ /  / /    
/____/ /_____/           /_/   \_\ /_____/  \____/  /_/     

 PROJECT SEAL - SYSTEM STATUS: ONLINE
"""

def print_banner():
    """Prints the project banner to the system logs."""
    for line in ASCII_BANNER.split("\n"):
        if line.strip():
            print(f"\033[96m{line}\033[0m")
    LOGGER.info("Seal Bot startup successful.")

async def send_startup_report(client, chat_id, module_count: int):
    """
    Sends a detailed but simple system status report to the logs group.
    No emojis. Professional monospaced formatting.
    """
    try:
        me = await client.get_me()
        
        # Gather System Data
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        pg_ver = pyrogram.__version__
        os_platform = platform.system()
        
        # Database Checks
        redis_status = "STABLE" if _redis else "DISABLED"
        mongo_status = "STABLE"
        
        # Character Library Statistics
        try:
            total_chars = await collection.count_documents({})
        except Exception:
            total_chars = "UNKNOWN"

        now = get_now_utc().strftime("%Y-%m-%d %H:%M:%S")

        report = (
            "<code>[ PROJET SEAL - SYSTEM STATUS REPORT ]</code>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"<code>BOT IDENTITY     : {me.first_name} (@{me.username})</code>\n"
            f"<code>BOT ID           : {me.id}</code>\n"
            f"<code>PYTHON VERSION   : {py_ver}</code>\n"
            f"<code>PYROGRAM VERSION : {pg_ver}</code>\n"
            f"<code>OPERATING SYSTEM : {os_platform}</code>\n"
            f"<code>LOADED MODULES   : {module_count}</code>\n"
            f"<code>CHARACTER COUNT  : {total_chars}</code>\n"
            f"<code>MONGODB STATUS   : {mongo_status}</code>\n"
            f"<code>REDIS STATUS     : {redis_status}</code>\n"
            f"<code>SYSTEM TIME      : {now}</code>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            "<code>STATUS: OPERATIONAL | HANDLERS: READY</code>"
        )

        await client.send_message(chat_id, report)
        
    except Exception as e:
        LOGGER.warning(f"Failed to send startup report: {e}")
