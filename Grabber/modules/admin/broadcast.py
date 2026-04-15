import asyncio

from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, OWNER_ID, app
from Grabber.database import group_collection, total_pm_users

# Rate limiter: max 25 concurrent sends at any time, with a short yield between
# each acquire to space out the API calls and stay safely under Telegram's limits.
_BROADCAST_SEM = asyncio.Semaphore(5)
_SEND_DELAY = 0.08   # ~12 sends/sec — safe, well below Telegram limit

async def _safe_forward(msg, target_id: int, max_retries: int = 3):
    """Forward a message to target_id with exponential backoff on FloodWait."""
    async with _BROADCAST_SEM:
        await asyncio.sleep(_SEND_DELAY)
        for attempt in range(max_retries):
            try:
                await msg.forward(target_id)
                return True
            except errors.FloodWait as e:
                wait = e.value + 2 * (2 ** attempt)
                LOGGER.warning(f"FloodWait {e.value}s — sleeping {wait}s (attempt {attempt+1})")
                await asyncio.sleep(wait)
            except (errors.UserIsBlocked, errors.PeerIdInvalid, errors.InputUserDeactivated):
                return "blocked"
            except (errors.ChatWriteForbidden, errors.ChatAdminRequired, errors.ChannelPrivate):
                return "forbidden"
            except Exception as e:
                LOGGER.error(f"Broadcast error sending to {target_id}: {e}")
                return False
        return False


@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ <b>Reply to a message to broadcast.</b>", parse_mode=ParseMode.HTML)

    cmd_parts = message.text.split()
    send_users = "-u" in cmd_parts
    send_groups = "-g" in cmd_parts

    if not send_users and not send_groups:
        send_users = send_groups = True

    msg = message.reply_to_message
    status = await message.reply_text("🚀 <b>Broadcast started...</b>", parse_mode=ParseMode.HTML)

    success_u = failed_u = success_g = failed_g = 0
    total_sent = 0
    blocked_users = []

    if send_users:
        async for user in total_pm_users.find({}, {"_id": 1}):
            user_id = user["_id"]
            result = await _safe_forward(msg, user_id)
            if result is True:
                success_u += 1
            elif result == "blocked":
                failed_u += 1
                blocked_users.append(user_id)
            else:
                failed_u += 1

            total_sent += 1
            if total_sent % 50 == 0:
                try:
                    await status.edit_text(
                        f"⏳ <b>Broadcasting...</b>\n"
                        f"👤 Users: <code>{success_u}</code> ok / <code>{failed_u}</code> fail",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass

        # Clean up unreachable users in bulk
        if blocked_users:
            await total_pm_users.delete_many({"_id": {"$in": blocked_users}})

    if send_groups:
        async for group in group_collection.find({}, {"group_id": 1}):
            group_id = group["group_id"]
            result = await _safe_forward(msg, group_id)
            if result is True:
                success_g += 1
            elif result == "forbidden":
                failed_g += 1
            else:
                failed_g += 1

            total_sent += 1
            if total_sent % 50 == 0:
                try:
                    await status.edit_text(
                        f"⏳ <b>Broadcasting...</b>\n"
                        f"👤 Users: <code>{success_u}</code>/<code>{success_u + failed_u}</code> "
                        f"👥 Groups: <code>{success_g}</code>/<code>{success_g + failed_g}</code>",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass

    summary = (
        "📊 <b>Broadcast Complete</b>\n\n"
        f"👤 <b>Users:</b> <code>{success_u}</code> ok / <code>{failed_u}</code> failed\n"
        f"👥 <b>Groups:</b> <code>{success_g}</code> ok / <code>{failed_g}</code> failed"
    )
    await status.edit_text(summary, parse_mode=ParseMode.HTML)

