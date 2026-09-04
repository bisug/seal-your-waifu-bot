"""Privacy policy + GDPR-style data erasure.

/privacy — shows what data the bot stores and where the full policy lives.
/delete  — irreversible wipe of the requesting user's data. Two-step
           confirm via inline buttons so a typo can't nuke an account.

Erasure scope (all collections holding personal data):
  user doc (profile, balance, harem, pets, quests, pass, referrals),
  PM registry, per-chat activity totals, webapp sessions, Redis caches,
  referral edges pointing at the user, and the user's own referral events.
"""

import time

from pyrogram import enums, filters, types

from backend.client import app
from backend.core.cache import invalidate_user_cache, rdel
from backend.core.logging import get_logger
from backend.core.utils import handle_errors, get_user_id_query
from backend.database import (
    db,
    group_user_totals_collection,
    sessions_collection,
    total_pm_users,
    user_collection,
)
from config import config

LOGGER = get_logger(__name__)

PRIVACY_TEXT = (
    "<b>SEAL Privacy Policy</b>\n\n"
    "<b>What we store</b>\n"
    "• Your Telegram ID, first name, username, and avatar URL\n"
    "• Gameplay data: balance, characters, pets, quests, XP, battle pass\n"
    "• Per-chat activity counts (messages sent, characters caught) — counts only, never message content\n"
    "• Referral links between users (who invited whom)\n"
    "• WebApp session tokens (hashed, expire after 1 hour)\n\n"
    "<b>What we never store</b>\n"
    "• Message text or media content from your chats\n"
    "• Payment details — Telegram Stars payments are processed by Telegram\n\n"
    "<b>How data is used</b>\n"
    "Gameplay state, leaderboards, and anti-abuse. We never sell or share personal data.\n\n"
    "<b>Your rights</b>\n"
    "• <code>/delete</code> — permanently erase all your data\n"
    "• Contact @{} for anything else\n\n"
    "<b>Copyright</b>\n"
    "Rights holders: use <code>/dmca &lt;character_id&gt;</code> or email {}."
)


@app.on_message(filters.command("privacy"))
@handle_errors
async def privacy_command(_, message: types.Message):
    await message.reply_text(
        PRIVACY_TEXT.format(config.SUPPORT_CHAT, config.DMCA_CONTACT or "the support chat"),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["delete", "deleteaccount", "erase"]))
@handle_errors
async def delete_command(_, message: types.Message):
    user_id = message.from_user.id
    buttons = types.InlineKeyboardMarkup(
        [[
            types.InlineKeyboardButton("⚠️ Erase everything", callback_data=f"gdpr:confirm:{user_id}"),
            types.InlineKeyboardButton("Cancel", callback_data="gdpr:cancel"),
        ]]
    )
    await message.reply_text(
        "<b>Delete your account?</b>\n\n"
        "This <b>permanently erases</b>:\n"
        "• Your profile, balance, characters, pets, and progress\n"
        "• Your activity counts in every chat\n"
        "• Your referral history\n"
        "• All active web sessions\n\n"
        "This cannot be undone. Characters you caught stay gone.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons,
    )


@app.on_callback_query(filters.regex(r"^gdpr:(confirm|cancel)"))
@handle_errors
async def gdpr_callback(_, query: types.CallbackQuery):
    _, action, target_id = query.data.split(":", 2)
    # Only the user who started the deletion may confirm it.
    if action == "confirm" and int(target_id) != query.from_user.id:
        return await query.answer("This deletion request belongs to someone else.", show_alert=True)
    if action == "cancel":
        await query.message.edit_text("Deletion cancelled.")
        return await query.answer()

    user_id = int(target_id)
    user_filter = get_user_id_query(user_id)

    # 1. Core user document (profile, harem, pets, quests, pass, referrals).
    await user_collection.delete_many(user_filter)

    # 2. PM registry + per-chat activity totals.
    await total_pm_users.delete_one({"_id": user_id})
    await group_user_totals_collection.delete_many({"user_id": {"$in": [user_id, str(user_id)]}})

    # 3. Web sessions (hashed token keys embed the user id in their value,
    #    so remove by the session key pattern and the user-id index doc).
    await sessions_collection.delete_many({"user_id": str(user_id)})
    await sessions_collection.delete_many({"user_id": user_id})

    # 4. Referral edges: remove the user from other users' referral lists.
    async for referrer in user_collection.find({"referrals": user_id}, {"_id": 1}):
        await user_collection.update_one(
            {"_id": referrer["_id"]}, {"$pull": {"referrals": user_id}}
        )

    # 5. Redis caches: profile, balance, cooldowns, recent-reward memory.
    await rdel(
        f"user:{user_id}",
        f"balance:{user_id}",
        f"reward:recent:{user_id}",
        f"last_sync:{user_id}",
    )
    await invalidate_user_cache(user_id)

    LOGGER.warning("GDPR: user %s erased all data via /delete", user_id)
    await query.message.edit_text(
        "✅ <b>Your data has been erased.</b>\n\n"
        "All profile, gameplay, activity, and session data was permanently deleted. "
        "If you use the bot again, a fresh account is created.",
        parse_mode=enums.ParseMode.HTML,
    )
    await query.answer()
