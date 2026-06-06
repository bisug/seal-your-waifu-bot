import asyncio
import base64
import binascii
import os
import tempfile
import urllib.parse
from datetime import datetime, timezone
from typing import Optional

import httpx
from pyrogram import enums
from pyrogram.errors import FloodWait

from Grabber import GALLERY_CHANNEL_ID, LOGGER, app
from Grabber.core.pets import get_pet_key, pet_id_from_name, upsert_catalog_pet
from Grabber.core.utils import html_escape, send_media_dynamic
from Grabber.core.waifu import (
    add_character_to_db,
    invalidate_character_cache,
    upload_media_safely,
)
from Grabber.modules.collection.rarities import RARITY_MAP

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_MEDIA_SCHEMES = {"http", "https"}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}
ALLOWED_EXTENSIONS = set(CONTENT_TYPE_EXTENSIONS.values())


class UploadError(ValueError):
    """Raised for user-correctable upload failures."""


def parse_character_rarity(value: int | str) -> str:
    if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
        rarity_num = int(value)
        rarity = RARITY_MAP.get(rarity_num)
        if rarity:
            return rarity
    value_str = str(value or "").strip()
    if value_str in RARITY_MAP.values():
        return value_str
    raise UploadError("Rarity must be a valid rarity number or rarity label.")


def parse_luck(value: float | int | str) -> float:
    value_str = str(value).strip().rstrip("%")
    try:
        luck = float(value_str)
    except (TypeError, ValueError) as exc:
        raise UploadError("Luck must be a number such as 0.12 or 12%.") from exc
    if luck > 1:
        luck = luck / 100
    if luck < 0 or luck > 0.35:
        raise UploadError("Luck must be between 0 and 35%.")
    return round(luck, 3)


def _safe_extension(raw_ext: str | None, content_type: str | None = None) -> str:
    ext = (raw_ext or "").lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = CONTENT_TYPE_EXTENSIONS.get((content_type or "").split(";")[0].strip().lower(), ".jpg")
    return ext if ext in ALLOWED_EXTENSIONS else ".jpg"


def _temp_file_path(prefix: str, ext: str) -> str:
    handle = tempfile.NamedTemporaryFile(prefix=f"{prefix}_", suffix=ext, delete=False)
    path = handle.name
    handle.close()
    return path


async def download_media_url(media_url: str, *, temp_prefix: str = "upload") -> str:
    parsed = urllib.parse.urlparse(str(media_url or "").strip())
    if parsed.scheme not in ALLOWED_MEDIA_SCHEMES:
        raise UploadError("Invalid media URL scheme. Only HTTP/HTTPS URLs are allowed.")

    ext = _safe_extension(os.path.splitext(parsed.path)[1])
    temp_path: Optional[str] = None
    downloaded_size = 0

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", media_url, timeout=20.0) as response:
                if response.status_code != 200:
                    raise UploadError(f"Failed to fetch media (HTTP {response.status_code}).")

                content_type = response.headers.get("Content-Type")
                ext = _safe_extension(ext, content_type)
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_UPLOAD_SIZE:
                    raise UploadError("File is too large. Max upload size is 10MB.")

                temp_path = _temp_file_path(temp_prefix, ext)
                with open(temp_path, "wb") as file_obj:
                    async for chunk in response.aiter_bytes():
                        downloaded_size += len(chunk)
                        if downloaded_size > MAX_UPLOAD_SIZE:
                            raise UploadError("File reached the 10MB limit and was stopped.")
                        file_obj.write(chunk)
        return temp_path
    except Exception:
        if temp_path and os.path.exists(temp_path):
            remove_temp_file(temp_path)
        raise


async def materialize_base64_media(
    media_data: str,
    *,
    filename: str | None = None,
    temp_prefix: str = "upload",
) -> str:
    data = str(media_data or "")
    content_type = None
    payload = data

    if data.startswith("data:"):
        header, sep, payload = data.partition(",")
        if not sep or ";base64" not in header:
            raise UploadError("Media data must be a base64 data URL.")
        content_type = header[5:].split(";")[0]

    try:
        media_bytes = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise UploadError("Media data is not valid base64.") from exc

    if not media_bytes:
        raise UploadError("Media file is empty.")
    if len(media_bytes) > MAX_UPLOAD_SIZE:
        raise UploadError("File is too large. Max upload size is 10MB.")

    ext = _safe_extension(os.path.splitext(filename or "")[1], content_type)
    temp_path = _temp_file_path(temp_prefix, ext)
    try:
        await asyncio.to_thread(_write_bytes, temp_path, media_bytes)
        return temp_path
    except Exception:
        remove_temp_file(temp_path)
        raise


def _write_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as file_obj:
        file_obj.write(data)


async def materialize_media_input(
    *,
    media_url: str | None = None,
    media_data: str | None = None,
    filename: str | None = None,
    temp_prefix: str = "upload",
) -> str:
    if media_data:
        return await materialize_base64_media(media_data, filename=filename, temp_prefix=temp_prefix)
    if media_url:
        return await download_media_url(media_url, temp_prefix=temp_prefix)
    raise UploadError("Provide either a media URL or uploaded media file.")


def remove_temp_file(temp_path: str | None) -> None:
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            LOGGER.debug("Failed to remove upload temp file: %s", temp_path)


async def upload_character_from_path(
    temp_path: str,
    *,
    name: str,
    anime: str,
    rarity: int | str,
    added_by_id: int,
    added_by_name: str,
) -> dict:
    char_name = str(name or "").strip().title()
    anime_name = str(anime or "").strip().title()
    if not char_name or not anime_name:
        raise UploadError("Character name and anime are required.")

    rarity_text = parse_character_rarity(rarity)
    final_url = await upload_media_safely(temp_path)
    if not final_url:
        raise UploadError("Media upload failed. Catbox/ImgBB rejected the file.")

    caption = (
        f"<b>Character Name:</b> {html_escape(char_name)}\n"
        f"<b>Anime Name:</b> {html_escape(anime_name)}\n"
        f"<b>Rarity:</b> {html_escape(rarity_text)}\n"
        f"Added by <a href=\"tg://user?id={added_by_id}\">{html_escape(added_by_name)}</a>"
    )

    try:
        sent_msg = await send_media_dynamic(
            client=app,
            chat_id=GALLERY_CHANNEL_ID,
            media_url=final_url,
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
        )
    except FloodWait as exc:
        LOGGER.warning("[Upload] FloodWait %ss - retrying gallery send once...", exc.value)
        await asyncio.sleep(exc.value + 2)
        sent_msg = await send_media_dynamic(
            client=app,
            chat_id=GALLERY_CHANNEL_ID,
            media_url=final_url,
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
        )

    char_data = {
        "img_url": final_url,
        "name": char_name,
        "anime": anime_name,
        "rarity": rarity_text,
        "message_id": sent_msg.id,
    }
    char_id = await add_character_to_db(char_data)
    invalidate_character_cache(rarity_text)
    return {**char_data, "id": char_id}


async def upload_pet_from_path(
    temp_path: str,
    *,
    name: str,
    rarity: str,
    hp: int,
    atk: int,
    spd: int,
    luck: float | int | str,
    ability: str,
    desc: str,
    zenith_price: int = 0,
    req_level: int = 0,
    petid: str | None = None,
    sort_order: int = 100,
    enabled: bool = True,
    uploaded_by: int | None = None,
) -> dict:
    pet_name = str(name or "").strip()
    if not pet_name:
        raise UploadError("Pet name is required.")

    final_url = await upload_media_safely(temp_path)
    if not final_url:
        raise UploadError("Media upload failed. Catbox/ImgBB rejected the file.")

    now = datetime.now(timezone.utc)
    normalized_petid = pet_id_from_name(petid) if petid else None
    pet_doc = {
        "petid": normalized_petid,
        "id": normalized_petid,
        "name": pet_name,
        "rarity": str(rarity or "Common").strip() or "Common",
        "hp": int(hp),
        "atk": int(atk),
        "spd": int(spd),
        "luck": parse_luck(luck),
        "ability": str(ability or "None").strip() or "None",
        "desc": str(desc or "").strip(),
        "img": final_url,
        "zenith_price": int(zenith_price),
        "req_level": int(req_level),
        "sort_order": int(sort_order),
        "enabled": bool(enabled),
        "updated_at": now,
    }
    if uploaded_by is not None:
        pet_doc["uploaded_by"] = int(uploaded_by)

    saved = await upsert_catalog_pet(pet_doc)
    return {**saved, "petid": get_pet_key(saved), "id": get_pet_key(saved)}
