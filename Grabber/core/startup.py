import sys
import platform
import logging
import pyrogram
import asyncio
from pyrogram import enums, errors
from Grabber.core.utils import get_now_utc
from Grabber.database import r as _redis, collection
from config import config

LOGGER = logging.getLogger(__name__)

# System Banner for Logs
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
    Sends a detailed system status report. 
    Attempts to send to the designated group, falling back to Owner PM if unavailable.
    """
    try:
        me = await client.get_me()
        
        # System Data Preparation
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        pg_ver = pyrogram.__version__
        os_platform = platform.system()
        os_arch = platform.machine()
        
        redis_status = "STABLE" if _redis else "DISABLED"
        mongo_status = "STABLE"
        
        try:
            total_chars = await collection.count_documents({})
        except Exception:
            total_chars = "UNKNOWN"

        now = get_now_utc().strftime("%Y-%m-%d %H:%M:%S")

        report = (
            "<code>[ PROJECT SEAL - SYSTEM STATUS REPORT ]</code>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"<code>BOT IDENTITY     : {me.first_name} (@{me.username})</code>\n"
            f"<code>BOT ID           : {me.id}</code>\n"
            f"<code>OWNER ID         : {config.OWNER_ID}</code>\n"
            f"<code>PYTHON VERSION   : {py_ver}</code>\n"
            f"<code>PYROGRAM VERSION : {pg_ver}</code>\n"
            f"<code>OPERATING SYSTEM : {os_platform} ({os_arch})</code>\n"
            f"<code>LOADED MODULES   : {module_count}</code>\n"
            f"<code>CHARACTER COUNT  : {total_chars}</code>\n"
            f"<code>MONGODB STATUS   : {mongo_status}</code>\n"
            f"<code>REDIS STATUS     : {redis_status}</code>\n"
            f"<code>SYSTEM TIME      : {now}</code>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            "<code>STATUS: OPERATIONAL | HANDLERS: READY</code>"
        )

        # Attempt to resolve peer and send message
        try:
            # For supergroups, get_chat can help "resolve" the peer for Pyrogram
            if isinstance(chat_id, int) and str(chat_id).startswith("-100"):
                try:
                    await client.get_chat(chat_id)
                except Exception:
                    pass
            
            await client.send_message(chat_id, report)
        except (errors.PeerIdInvalid, errors.ChannelInvalid, errors.ChatWriteForbidden):
            LOGGER.warning(f"Dedicated Logs Group ({chat_id}) inaccessible. Falling back to Owner PM.")
            await client.send_message(config.OWNER_ID, f"⚠️ <b>Logs Group Inaccessible</b>\n\n{report}")
        except Exception as e:
            LOGGER.error(f"Startup report primary delivery failed: {e}")
            await client.send_message(config.OWNER_ID, report)
            
    except Exception as e:
        LOGGER.warning(f"Critical failure in startup report logic: {e}")
