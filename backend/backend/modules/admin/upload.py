import os
import shlex

from pyrogram import enums, filters, types
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from backend import sudo_filter, uploader_filter
from backend.client import app
from backend.core.logging import get_logger
from backend.core.roles import format_upload_reward, grant_upload_reward
from backend.core.uploads import (
    UploadError,
    download_media_url,
    parse_luck,
    remove_temp_file,
    temp_download_dir,
    upload_character_from_path,
    upload_pet_from_path,
)
from backend.core.utils import handle_errors, html_escape
from backend.database import collection
from backend.modules.collection.rarities import RARITY_MAP
from config import config

LOGGER = get_logger(__name__)


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


def get_pet_upload_help():
    return (
        "<b>Format:</b>\n"
        "Reply to media:\n"
        "<code>/uploadpet \"Name\" \"Rarity\" HP ATK SPD Luck Price ReqLevel \"Ability\" \"Description\" [petid] [sort_order] [enabled]</code>\n\n"
        "With URL:\n"
        "<code>/uploadpet URL \"Name\" \"Rarity\" HP ATK SPD Luck Price ReqLevel \"Ability\" \"Description\" [petid] [sort_order] [enabled]</code>\n\n"
        "Luck accepts decimals or percent values, for example <code>0.12</code> or <code>12%</code>."
    )


def _message_has_upload_media(message: types.Message | None) -> bool:
    return bool(
        message
        and (
            message.photo
            or message.document
            or getattr(message, "video", None)
            or getattr(message, "animation", None)
        )
    )


def _parse_command_args(message: types.Message) -> list[str] | None:
    cmd_text = message.text or message.caption
    if not cmd_text:
        return None
    return shlex.split(cmd_text)[1:]


async def _materialize_message_media(
    message: types.Message,
    *,
    media_url: str | None,
    is_reply: bool,
    status: types.Message,
    temp_prefix: str,
) -> str:
    if is_reply:
        await status.edit_text("📥 Downloading media from Telegram...")
        # Absolute dir: kurigram 2.2.25 resolves relative paths against workdir.
        temp_path = await message.reply_to_message.download(file_name=temp_download_dir(temp_prefix) + "/")
        if not temp_path or not os.path.exists(temp_path):
            raise UploadError("Failed to retrieve Telegram media.")
        return temp_path

    await status.edit_text("📥 Fetching media from URL (10MB limit)...")
    return await download_media_url(media_url or "", temp_prefix=temp_prefix)


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


def _split_media_args(args: list[str], is_reply: bool, required_count: int) -> tuple[str | None, list[str]]:
    if is_reply:
        values = args
        media_url = None
    else:
        if len(args) < required_count + 1:
            raise UploadError("Missing media URL or required fields.")
        media_url = args[0]
        values = args[1:]

    if len(values) < required_count:
        raise UploadError("Missing required fields.")
    return media_url, values


@app.on_message(filters.command("upload") & uploader_filter)
@handle_errors
async def upload_waifu_handler(_, message: types.Message):
    try:
        args = _parse_command_args(message)
    except ValueError as e:
        return await message.reply_text(f"❌ <b>Parsing Error:</b> {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)

    if args is None:
        return

    is_reply = _message_has_upload_media(message.reply_to_message)
    try:
        media_url, values = _split_media_args(args, is_reply, 3)
        name, anime, rarity = values[0], values[1], values[2]
    except UploadError:
        return await message.reply_text(get_rarity_help(), parse_mode=enums.ParseMode.HTML)

    status = await message.reply_text("⏳ <b>Processing upload...</b>", parse_mode=enums.ParseMode.HTML)
    temp_path = None

    try:
        temp_path = await _materialize_message_media(
            message,
            media_url=media_url,
            is_reply=is_reply,
            status=status,
            temp_prefix=f"tg_char_{message.id}",
        )
        await status.edit_text("☁️ Uploading media to secure host...")
        character = await upload_character_from_path(
            temp_path,
            name=name,
            anime=anime,
            rarity=rarity,
            added_by_id=message.from_user.id,
            added_by_name=message.from_user.first_name,
        )
        final_url = character["img_url"]
        reward = await grant_upload_reward(message.from_user.id, source="bot_character")
        reward_text = format_upload_reward(reward)
        reward_line = f"\nReward: <code>{html_escape(reward_text)}</code>" if reward_text else ""
        await status.edit_text(
            f"✅ <b>Waifu Uploaded!</b>\n"
            f"ID: <code>{character['id']}</code>\n"
            f"Name: {html_escape(character['name'])}\n"
            f"Host: {'Catbox' if 'catbox' in final_url else 'ImgBB'}"
            f"{reward_line}",
            parse_mode=enums.ParseMode.HTML,
        )
    except UploadError as e:
        await status.edit_text(f"❌ {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error("Upload Failure: %s", e, exc_info=True)
        await status.edit_text(f"❌ Error: {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)
    finally:
        remove_temp_file(temp_path)


@app.on_message(filters.command("uploadpet") & uploader_filter)
@handle_errors
async def upload_pet_handler(_, message: types.Message):
    try:
        args = _parse_command_args(message)
    except ValueError as e:
        return await message.reply_text(f"❌ <b>Parsing Error:</b> {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)

    if args is None:
        return

    is_reply = _message_has_upload_media(message.reply_to_message)
    try:
        media_url, values = _split_media_args(args, is_reply, 10)
        name, rarity, hp, atk, spd, luck, price, req_level, ability, desc = values[:10]
        petid = values[10] if len(values) > 10 and values[10].lower() not in {"-", "auto", "none"} else None
        sort_order = int(values[11]) if len(values) > 11 else 100
        enabled = _parse_bool(values[12]) if len(values) > 12 else True
        hp = int(hp)
        atk = int(atk)
        spd = int(spd)
        price = int(price)
        req_level = int(req_level)
        parse_luck(luck)
    except (UploadError, ValueError):
        return await message.reply_text(get_pet_upload_help(), parse_mode=enums.ParseMode.HTML)

    status = await message.reply_text("⏳ <b>Processing pet upload...</b>", parse_mode=enums.ParseMode.HTML)
    temp_path = None

    try:
        temp_path = await _materialize_message_media(
            message,
            media_url=media_url,
            is_reply=is_reply,
            status=status,
            temp_prefix=f"tg_pet_{message.id}",
        )
        await status.edit_text("☁️ Uploading pet media to secure host...")
        pet = await upload_pet_from_path(
            temp_path,
            name=name,
            petid=petid,
            rarity=rarity,
            hp=hp,
            atk=atk,
            spd=spd,
            luck=luck,
            ability=ability,
            desc=desc,
            zenith_price=price,
            req_level=req_level,
            sort_order=sort_order,
            enabled=enabled,
            uploaded_by=message.from_user.id,
        )
        reward = await grant_upload_reward(message.from_user.id, source="bot_pet")
        reward_text = format_upload_reward(reward)
        reward_line = f"\nReward: <code>{html_escape(reward_text)}</code>" if reward_text else ""
        await status.edit_text(
            f"✅ <b>Pet Uploaded!</b>\n"
            f"ID: <code>{html_escape(pet['petid'])}</code>\n"
            f"Name: {html_escape(pet['name'])}\n"
            f"Price: <code>{pet['zenith_price']}</code> Zenith\n"
            f"Enabled: <code>{str(pet['enabled'])}</code>"
            f"{reward_line}",
            parse_mode=enums.ParseMode.HTML,
        )
    except UploadError as e:
        await status.edit_text(f"❌ {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error("Pet Upload Failure: %s", e, exc_info=True)
        await status.edit_text(f"❌ Error: {html_escape(str(e))}", parse_mode=enums.ParseMode.HTML)
    finally:
        remove_temp_file(temp_path)


@app.on_message(filters.command(["delete", "del"]) & sudo_filter)
@handle_errors
async def delete_waifu_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: <code>/delete &lt;id&gt;</code>", parse_mode=enums.ParseMode.HTML)
    raw_id = message.command[1]
    char_id = raw_id.zfill(2) if raw_id.isdigit() else raw_id
    character = await collection.find_one({"id": char_id})
    if not character:
        return await message.reply_text(f"❌ Character not found with ID: <code>{char_id}</code>", parse_mode=enums.ParseMode.HTML)
    text = (
        f"⚠️ <b>Delete Confirmation</b>\n\n"
        f"Are you sure you want to delete this character?\n\n"
        f"🆔 ID: <code>{char_id}</code>\n"
        f"📛 Name: <b>{html_escape(character['name'])}</b>\n"
        f"🎬 Anime: {html_escape(character['anime'])}\n"
        f"🔮 Rarity: {html_escape(character['rarity'])}"
    )
    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"del_confirm:{char_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="del_cancel"),
        ]
    ]
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
    )


@app.on_callback_query(filters.regex(r"^del_") & sudo_filter)
async def delete_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    action = data[0]
    if action == "del_cancel":
        await query.message.delete()
        return await query.answer("Deletion cancelled.")
    if action == "del_confirm":
        char_id = data[1]
        character = await collection.find_one_and_delete({"id": char_id})
        if character:
            msg_id = character.get("message_id")
            if msg_id:
                try:
                    await app.delete_messages(config.GALLERY_CHANNEL_ID, msg_id)
                except Exception as e:
                    LOGGER.debug(f"Failed to delete gallery message {msg_id}: {e}")
            from backend.core.waifu import invalidate_character_cache

            invalidate_character_cache(character.get("rarity"))
            await query.message.edit_text(
                f"✅ <b>Successfully Deleted!</b>\n"
                f"ID: <code>{char_id}</code>\n"
                f"Name: <b>{html_escape(character['name'])}</b>",
                parse_mode=enums.ParseMode.HTML,
            )
            await query.answer("Character deleted.")
        else:
            await query.answer("❌ Error: Character not found or already deleted.", show_alert=True)
            await query.message.delete()
