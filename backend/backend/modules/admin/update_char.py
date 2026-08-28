import json
import os
import shlex
import uuid
from collections import OrderedDict
import httpx
from pyrogram import enums, filters, types
from config import config
from backend import GALLERY_CHANNEL_ID, LOGGER, app, sudo_filter
from backend.core.cache import rdel, rget, rset
from backend.core.utils import handle_errors, html_escape
from backend.core.waifu import (get_character_by_id, invalidate_character_cache,
                                upload_media_safely)
from backend.database import collection
from backend.modules.collection.rarities import RARITY_MAP
LOG_GROUP_ID = config.LOG_GROUP_ID
_MAX_PENDING_UPDATES = 1000
_pending_updates: OrderedDict[str, dict] = OrderedDict()


def _remember_update(proposal_id: str, proposal_data: dict):
    _pending_updates[proposal_id] = proposal_data
    _pending_updates.move_to_end(proposal_id)
    while len(_pending_updates) > _MAX_PENDING_UPDATES:
        _pending_updates.popitem(last=False)


def _forget_update(proposal_id: str):
    _pending_updates.pop(proposal_id, None)


def get_rarity_help():
    """Generates dynamic rarity map help text."""
    rarity_list = "\n".join([f"({v}={k})" for k, v in RARITY_MAP.items()])
    return (
        "<b>Format:</b>\n"
        "Reply to media: <code>/upload \"Name\" \"Anime\" RarityNum</code>\n"
        "With URL: <code>/upload URL \"Name\" \"Anime\" RarityNum</code>\n\n"
        "<b>Rarity Map:</b>\n"
        f"{rarity_list}"
    )
@app.on_message(filters.command("update") & sudo_filter)
@handle_errors
async def update_waifu_handler(_, message: types.Message):
    """
    Parses /update <id> field="value" ...
    Displays a proposal in LOG_GROUP_ID for confirmation.
    """
    cmd_text = message.text or message.caption
    if not cmd_text:
        return
    try:
        # 1. Parse Key-Value Pairs using shlex
        cmd_args = shlex.split(cmd_text)[1:]
    except ValueError as e:
        return await message.reply_text(f"❌ <b>Parsing Error:</b> {e}")
    if len(cmd_args) < 2:
        return await message.reply_text(
            "❌ <b>Usage:</b>\n<code>/update &lt;id&gt; name=\"New Name\" anime=\"New Anime\" rarity=5 url=\"new_url\"</code>",
            parse_mode=enums.ParseMode.HTML
        )
    char_id = cmd_args[0]
    character = await get_character_by_id(char_id)
    if not character:
        return await message.reply_text("❌ Character not found.")
    updates = {}
    remaining_args = cmd_args[1:]
    for arg in remaining_args:
        if "=" not in arg:
            continue
        key, val = arg.split("=", 1)
        key = key.lower().strip()
        val = val.strip()
        if key == "name":
            updates['name'] = val.title()
        elif key == "anime":
            updates['anime'] = val.title()
        elif key == "rarity":
            try:
                r_num = int(val)
                if r_num not in RARITY_MAP:
                    raise ValueError
                updates['rarity'] = RARITY_MAP[r_num]
                updates['rarity_id'] = r_num
            except ValueError:
                return await message.reply_text(f"❌ Invalid rarity number. Map: {get_rarity_help()}")
        elif key in ("url", "img_url"):
            if not (val.startswith("http://") or val.startswith("https://")):
                 return await message.reply_text("❌ Invalid URL scheme.")
            updates['img_url'] = val
    if not updates:
        return await message.reply_text("❌ No valid fields to update provided.")
    # 2. Prepare Proposal
    proposal_id = str(uuid.uuid4())[:8]
    proposal_data = {
        'char_id': char_id,
        'updates': updates,
        'old': {
            'name': character['name'],
            'anime': character['anime'],
            'rarity': character['rarity'],
            'img_url': character['img_url']
        }
    }
    # Store in Redis for 1 hour with bounded in-process fallback.
    await rset(f"upd:{proposal_id}", json.dumps(proposal_data), 3600)
    _remember_update(proposal_id, proposal_data)
    # 3. Format Proposal Message
    diff_text = f"<b>🆕 Update Proposal for ID:</b> <code>{char_id}</code>\n\n"
    for k, new_v in updates.items():
        old_v = proposal_data['old'].get(k)
        diff_text += f"🔹 <b>{k.title()}:</b>\n  <s>{html_escape(str(old_v))}</s>\n  ➡️ <code>{html_escape(str(new_v))}</code>\n\n"
    diff_text += f"Proposed by <a href=\"tg://user?id={message.from_user.id}\">{html_escape(message.from_user.first_name)}</a>"
    buttons = [
        [
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"upd_cnf:{proposal_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"upd_can:{proposal_id}")
        ]
    ]
    try:
        preview_url = updates.get('img_url', character['img_url'])
        await app.send_media_safe(
            chat_id=LOG_GROUP_ID,
            media_url=preview_url,
            caption=diff_text,
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        await message.reply_text(f"⏳ Proposal sent to Logger group (ID: <code>{proposal_id}</code>).", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Proposal Failure: {e}")
        await message.reply_text(f"❌ Failed to send proposal: {e}")
@app.on_callback_query(filters.regex(r"^upd_(cnf|can):"))
async def update_callback_handler(_, query: types.CallbackQuery):
    action, prop_id = query.data.split(":")
    raw_data = await rget(f"upd:{prop_id}")
    data = json.loads(raw_data) if raw_data else _pending_updates.get(prop_id)
    if not data:
        await query.answer("⌛ Proposal expired or not found.", show_alert=True)
        return await query.message.delete()
    if action == "can":
        await query.answer("❌ Update cancelled.")
        await rdel(f"upd:{prop_id}")
        _forget_update(prop_id)
        return await query.message.delete()
    # 2. Confirm Action
    await query.answer("⚙️ Applying changes...", show_alert=True)
    char_id = data['char_id']
    updates = data['updates']
    status_msg = await app.send_message_safe(LOG_GROUP_ID, f"⏳ Processing Update for <code>{char_id}</code>...")
    try:
        # Re-host media if URL changed
        if 'img_url' in updates:
            temp_path = f"temp_upd_{char_id}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(updates['img_url'], timeout=20.0)
                if resp.status_code == 200:
                    with open(temp_path, "wb") as f:
                        f.write(resp.content)
                    final_url = await upload_media_safely(temp_path)
                    if os.path.exists(temp_path): os.remove(temp_path)
                    if final_url:
                        updates['img_url'] = final_url
                    else:
                        raise Exception("Re-hosting failed.")
                else:
                    raise Exception(f"Failed to fetch new image (HTTP {resp.status_code})")
        # Update Database
        await collection.update_one({'id': char_id}, {'$set': updates})
        # Refetch full char for gallery update
        updated_char = await get_character_by_id(char_id)
        invalidate_character_cache(data['old']['rarity'])
        if 'rarity' in updates:
            invalidate_character_cache(updates['rarity'])
        # Update Gallery Channel Message
        msg_id = updated_char.get('message_id')
        if msg_id:
            new_caption = (
                f"<b>Character Name:</b> {updated_char['name']}\n"
                f"<b>Anime Name:</b> {updated_char['anime']}\n"
                f"<b>Rarity:</b> {updated_char['rarity']}\n"
                f"<i>(Updated by Admin)</i>"
            )
            try:
                if 'img_url' in updates:
                    # Change media and caption
                    media_type = "video" if updates['img_url'].endswith(('.mp4', '.webm', '.gif')) else "photo"
                    await app.edit_message_media(
                        chat_id=GALLERY_CHANNEL_ID,
                        message_id=msg_id,
                        media=types.InputMedia(
                            media=updates['img_url'],
                            caption=new_caption,
                            parse_mode=enums.ParseMode.HTML,
                            type=media_type
                        )
                    )
                else:
                    # Just caption
                    await app.edit_message_caption(
                        chat_id=GALLERY_CHANNEL_ID,
                        message_id=msg_id,
                        caption=new_caption,
                        parse_mode=enums.ParseMode.HTML
                    )
            except Exception as me:
                LOGGER.warning(f"Gallery Edit Failed for {char_id}: {me}")
        await status_msg.edit_text(f"✅ <b>Character {char_id} Updated!</b>\n\n" + 
                                 "\n".join([f"• {k}: {v}" for k, v in updates.items()]))
        await query.message.delete()
        await rdel(f"upd:{prop_id}")
        _forget_update(prop_id)
    except Exception as e:
        LOGGER.error(f"Update Confirmation Error: {e}")
        await status_msg.edit_text(f"❌ <b>Update Failed:</b> {html_escape(str(e))}")
