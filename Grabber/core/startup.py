import asyncio
import logging
import platform
import sys
import pyrogram
from pyrogram import Client, enums, errors
from config import config
from Grabber.core.utils import get_now_utc
from Grabber.database import collection
from Grabber.database import r as _redis
LOGGER = logging.getLogger(__name__)
async def send_startup_report(client: Client, chat_id: int, module_count: int) -> None:
    """
    Send a clean system status report to a logs group (fallback to owner PM).
    """
    try:
        me = await client.get_me()
        # System info
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        pg_ver = pyrogram.__version__
        os_platform = platform.system()
        os_arch = platform.machine()
        # Redis status
        redis_status = "❌ DISCONNECTED"
        if _redis:
            try:
                redis_status = "✅ CONNECTED" if await asyncio.wait_for(_redis.ping(), timeout=3.0) else "❌ DISCONNECTED"
            except Exception as redis_err:
                LOGGER.warning(f"Redis health check failed: {redis_err}")
        # MongoDB status & character count
        mongo_status = "❌ DISCONNECTED"
        total_chars = "UNKNOWN"
        try:
            total_chars = await collection.count_documents({})
            mongo_status = "✅ CONNECTED"
        except Exception as db_err:
            LOGGER.warning(f"MongoDB health check failed: {db_err}")
        now = get_now_utc().strftime("%Y-%m-%d %H:%M:%S")
        # Clean, modern report without decorative lines
        report = (
            f"<b>📡 PROJECT SEAL · SYSTEM STATUS</b>\n"
            f"<code>Bot</code>        → {me.first_name} (@{me.username})  <code>({me.id})</code>\n"
            f"<code>Owner</code>      → <code>{config.OWNER_ID}</code>\n"
            f"<code>Python</code>     → {py_ver}\n"
            f"<code>Kurigram</code>   → {pg_ver}\n"
            f"<code>OS</code>         → {os_platform} ({os_arch})\n"
            f"<code>Modules</code>    → {module_count} loaded\n"
            f"<code>Characters</code> → {total_chars}\n"
            f"<code>MongoDB</code>    → {mongo_status}\n"
            f"<code>Redis</code>      → {redis_status}\n"
            f"<code>System time</code>→ {now}\n"
            f"\n✨ <b>STATUS: OPERATIONAL · HANDLERS READY</b>"
        )
        # Try sending to logs group, fallback to owner
        try:
            await client.send_message(chat_id, report, parse_mode=enums.ParseMode.HTML)
        except (errors.PeerIdInvalid, errors.ChannelInvalid, errors.ChatWriteForbidden) as e:
            LOGGER.warning(f"Logs group {chat_id} inaccessible: {e}. Falling back to owner PM.")
            fallback_msg = f"⚠️ <b>Logs group unreachable</b>\n\n{report}"
            await client.send_message(config.OWNER_ID, fallback_msg, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"Unexpected error sending startup report: {e}")
            await client.send_message(config.OWNER_ID, report, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.critical(f"Failed to generate startup report: {e}")
        try:
            await client.send_message(
                config.OWNER_ID,
                f"❌ <b>Startup report failed</b>\nError: {e}",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            LOGGER.critical("Could not notify owner about startup failure.")
