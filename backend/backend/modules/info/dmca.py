"""DMCA / takedown handling.

Copyright complaints arrive via /dmca in the bot or the webapp contact route.
Each report is logged, the reported character is removed immediately
(best-effort removal while the report is reviewed), and the cache is
invalidated so it stops spawning instantly.

ponytail: single-claimant removal is a manual-trust ceiling — a hostile
reporter could de-list characters they dislike. Upgrade path: require a
signed statement field + restore window before deletion becomes permanent.
"""

import time

from pyrogram import enums, filters, types

from backend.client import app
from backend.core.logging import get_logger
from backend.core.utils import handle_errors, html_escape
from backend.core.waifu import invalidate_character_cache
from backend.database import collection, takedown_log_collection
from config import config

LOGGER = get_logger(__name__)

DMCA_CONTACT = config.DMCA_CONTACT


@app.on_message(filters.command("dmca"))
@handle_errors
async def dmca_command(_, message: types.Message):
    """Report copyright infringement. Usage: /dmca <character_id> [details]"""
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Copyright / Takedown Report</b>\n\n"
            "To report content you believe infringes your copyright:\n"
            "1. Send <code>/dmca &lt;character_id&gt;</code> (ID shown on the character card)\n"
            "2. Or email us with the character ID and proof of ownership\n\n"
            f"📧 Contact: <code>{DMCA_CONTACT or 'set DMCA_CONTACT in bot config'}</code>\n\n"
            "Reports are actioned within 48 hours. Content is removed from "
            "spawns and the gallery while under review.",
            parse_mode=enums.ParseMode.HTML,
        )
    char_id = message.command[1].strip()
    details = " ".join(message.command[2:]).strip() or "no details provided"
    reporter = message.from_user

    char = await collection.find_one({"id": char_id})
    if not char:
        return await message.reply_text(
            f"No character found with ID <code>{html_escape(char_id)}</code>. "
            "Check the ID on the character card and try again.",
            parse_mode=enums.ParseMode.HTML,
        )

    # Log the report first — even if removal fails, the record exists.
    report = {
        "character_id": char_id,
        "character_name": char.get("name"),
        "anime": char.get("anime"),
        "reporter_id": reporter.id,
        "reporter_name": reporter.first_name,
        "details": details,
        "reported_at": time.time(),
        "status": "removed",
    }
    await takedown_log_collection.insert_one(report)

    # Remove the character and stop it spawning.
    await collection.delete_one({"id": char_id})
    invalidate_character_cache(char.get("rarity"))

    LOGGER.warning("DMCA: removed character %s (%s / %s) reported by %s",
                   char_id, char.get("name"), char.get("anime"), reporter.id)

    await message.reply_text(
        "✅ <b>Report received.</b>\n\n"
        f"Character <code>{html_escape(char_id)}</code> has been removed from the bot "
        "while we review your claim.\n\n"
        "If you are the rights holder, please send proof of ownership to "
        f"<code>{DMCA_CONTACT or 'the support chat'}</code> within 7 days so we can "
        "close this report. Thank you for helping keep SEAL compliant.",
        parse_mode=enums.ParseMode.HTML,
    )
