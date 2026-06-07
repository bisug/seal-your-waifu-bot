import asyncio
import logging
import platform
import sys
import pyrogram
from pyrogram import Client, enums, errors
from config import config
from Grabber.core.utils import get_now_utc, html_escape
from Grabber.database import collection
from Grabber.database import r as _redis
LOGGER = logging.getLogger(__name__)


def _status_text(value) -> str:
    if value is None:
        return "unknown"
    return html_escape(str(value))


def _format_bot_status(label: str, status: dict | str | None) -> list[str]:
    if not isinstance(status, dict):
        return [f"<code>{label}</code> → {_status_text(status)}"]

    state = status.get("state", "unknown")
    command_state = "n/a"
    if status.get("commands_synced"):
        command_state = "synced"
    elif status.get("command_sync_error"):
        command_state = f"failed ({status.get('command_sync_error')})"

    identity = ""
    username = status.get("username")
    bot_id = status.get("id")
    if username:
        identity = f" @{html_escape(username)}"
    if bot_id:
        identity = f"{identity} <code>({html_escape(str(bot_id))})</code>"

    line = (
        f"<code>{label}</code> → {_status_text(state)}{identity}"
        f" | commands: {_status_text(command_state)}"
        f" | modules: {_status_text(status.get('modules_loaded', 0))}"
    )
    failed_modules = status.get("modules_failed") or []
    if failed_modules:
        line = f"{line} | failed modules: <b>{len(failed_modules)}</b>"
    if status.get("error"):
        line = f"{line} | error: {_status_text(status.get('error'))}"
    return [line]


def _format_startup_status(startup_status: dict | None) -> list[str]:
    if not startup_status:
        return []
    lines = [
        f"<code>Startup</code>    → {_status_text(startup_status.get('startup'))}",
        f"<code>Sudo roles</code> → {_status_text(startup_status.get('sudo_users'))}",
        f"<code>Indexes</code>    → {_status_text(startup_status.get('indexes'))}",
        f"<code>Pet catalog</code>→ {_status_text(startup_status.get('pet_catalog'))}",
        f"<code>Monitor</code>    → {_status_text(startup_status.get('resource_monitor'))}",
    ]
    lines.extend(_format_bot_status("MainBot", startup_status.get("main_bot")))
    lines.extend(_format_bot_status("GameBot", startup_status.get("game_bot")))
    lines.extend(_format_bot_status("UserBot", startup_status.get("userbot")))
    return lines


async def send_startup_report(
    client: Client,
    chat_id: int,
    module_count: int,
    startup_status: dict | None = None,
) -> None:
    """
    Send a clean system status report to a logs group (fallback to owner PM).
    """
    try:
        me = await client.get_me()
        bot_username = f"@{html_escape(me.username)}" if me.username else "(no username)"
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
        startup_lines = _format_startup_status(startup_status)
        status_block = f"\n" + "\n".join(startup_lines) if startup_lines else ""
        startup_state = (startup_status or {}).get("startup", "operational")
        status_label = "OPERATIONAL" if startup_state == "operational" else f"DEGRADED · {_status_text(startup_state).upper()}"
        # Clean, modern report without decorative lines
        report = (
            f"<b>📡 PROJECT SEAL · SYSTEM STATUS</b>\n"
            f"<code>Bot</code>        → {html_escape(me.first_name)} ({bot_username})  <code>({me.id})</code>\n"
            f"<code>Owner</code>      → <code>{config.OWNER_ID}</code>\n"
            f"<code>Python</code>     → {py_ver}\n"
            f"<code>Kurigram</code>   → {pg_ver}\n"
            f"<code>OS</code>         → {os_platform} ({os_arch})\n"
            f"<code>Modules</code>    → {module_count} loaded\n"
            f"<code>Characters</code> → {total_chars}\n"
            f"<code>MongoDB</code>    → {mongo_status}\n"
            f"<code>Redis</code>      → {redis_status}\n"
            f"<code>System time</code>→ {now}\n"
            f"{status_block}"
            f"\n\n✨ <b>STATUS: {status_label}</b>"
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
                f"❌ <b>Startup report failed</b>\nError: {html_escape(str(e))}",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            LOGGER.critical("Could not notify owner about startup failure.")
