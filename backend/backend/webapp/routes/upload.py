import re
from typing import Annotated, Any, Optional
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.logging import get_logger
from backend.core.roles import format_upload_reward, get_role_payload, grant_upload_reward
from backend.core.uploads import (
    ALLOWED_EXTENSIONS,
    CONTENT_TYPE_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    UploadError,
    materialize_media_input,
    parse_luck,
    remove_temp_file,
    upload_character_from_path,
    upload_pet_from_path,
)
from backend.core.utils import get_user_id_query
from backend.core.waifu import invalidate_character_cache
from backend.database import collection, user_collection
from backend.modules.collection.rarities import RARITY_MAP
from backend.webapp.auth import require_sudo_user, require_uploader_user

LOGGER = get_logger(__name__)

router = APIRouter()

CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
CHAR_ID_PATTERN = r"^[A-Za-z0-9_-]{1,80}$"
FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,180}$")
MAX_MEDIA_DATA_CHARS = ((MAX_UPLOAD_SIZE + 2) // 3) * 4 + 128
MEDIA_URL_SCHEMES = {"http", "https"}
IMAGE_URL_SCHEMES = {"https"}


def _clean_text(value: Any, label: str, *, allow_blank: bool = False) -> str:
    text = str(value or "").strip()
    if not text and not allow_blank:
        raise ValueError(f"{label} cannot be blank")
    if CONTROL_CHAR_RE.search(text):
        raise ValueError(f"{label} contains invalid control characters")
    return text


def _clean_optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    text = _clean_text(value, label, allow_blank=True)
    return text or None


def _normalize_character_rarity_value(value: int | str | None) -> str:
    if value is None:
        raise ValueError("Invalid rarity")

    if isinstance(value, int):
        rarity = RARITY_MAP.get(value)
        if not rarity:
            raise ValueError("Invalid rarity")
        return rarity

    text = str(value).strip()
    if not text:
        raise ValueError("Invalid rarity")
    if text.isdigit():
        rarity = RARITY_MAP.get(int(text))
        if not rarity:
            raise ValueError("Invalid rarity")
        return rarity
    if text not in set(RARITY_MAP.values()):
        raise ValueError("Invalid rarity")
    return text


def _validate_url(value: Any, label: str, *, schemes: set[str]) -> str | None:
    text = _clean_optional_text(value, label)
    if text is None:
        return None

    parsed = urlparse(text)
    if parsed.scheme not in schemes:
        allowed = "/".join(sorted(schemes))
        raise ValueError(f"{label} must use {allowed}")
    if not parsed.hostname:
        raise ValueError(f"{label} must include a valid hostname")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} must not include credentials")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError(f"{label} has an invalid port") from exc
    if parsed.fragment:
        text = urlunparse(parsed._replace(fragment=""))
    return text


class StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MediaUploadPayload(StrictPayload):
    media_url: Optional[str] = Field(default=None, max_length=2048)
    media_data: Optional[str] = Field(default=None, max_length=MAX_MEDIA_DATA_CHARS)
    filename: Optional[str] = Field(default=None, max_length=180)

    @field_validator("media_url", mode="before")
    @classmethod
    def validate_media_url(cls, value: Any) -> str | None:
        return _validate_url(value, "Media URL", schemes=MEDIA_URL_SCHEMES)

    @field_validator("media_data", mode="before")
    @classmethod
    def validate_media_data(cls, value: Any) -> str | None:
        text = _clean_optional_text(value, "Media data")
        if text is None:
            return None
        if len(text) > MAX_MEDIA_DATA_CHARS:
            raise ValueError("Media data is too large")
        if text.startswith("data:"):
            header, sep, _ = text.partition(",")
            if not sep or ";base64" not in header:
                raise ValueError("Media data must be a base64 data URL")
            content_type = header[5:].split(";")[0].strip().lower()
            if content_type not in CONTENT_TYPE_EXTENSIONS:
                raise ValueError("Media data type is not supported")
        return text

    @field_validator("filename", mode="before")
    @classmethod
    def validate_filename(cls, value: Any) -> str | None:
        text = _clean_optional_text(value, "Filename")
        if text is None:
            return None
        if not FILENAME_RE.fullmatch(text) or text in {".", ".."}:
            raise ValueError("Filename contains unsupported characters")
        ext = text[text.rfind("."):].lower() if "." in text else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Filename extension is not supported")
        return text

    @model_validator(mode="after")
    def validate_media_source(self):
        has_url = bool(self.media_url)
        has_data = bool(self.media_data)
        if has_url == has_data:
            raise ValueError("Provide exactly one media source: media_url or media_data")
        return self


class CharacterUploadPayload(MediaUploadPayload):
    name: str = Field(..., min_length=1, max_length=120)
    anime: str = Field(..., min_length=1, max_length=120)
    rarity: int | str

    @field_validator("name", "anime", mode="before")
    @classmethod
    def validate_character_text(cls, value: Any, info) -> str:
        return _clean_text(value, info.field_name.replace("_", " ").title())

    @field_validator("rarity", mode="before")
    @classmethod
    def validate_rarity(cls, value: Any) -> str:
        return _normalize_character_rarity_value(value)


class CharacterEditPayload(StrictPayload):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    anime: Optional[str] = Field(default=None, min_length=1, max_length=120)
    rarity: Optional[int | str] = None
    img_url: Optional[str] = Field(default=None, min_length=1, max_length=1000)

    @field_validator("name", "anime", mode="before")
    @classmethod
    def validate_optional_character_text(cls, value: Any, info) -> str | None:
        if value is None:
            return None
        return _clean_text(value, info.field_name.replace("_", " ").title())

    @field_validator("rarity", mode="before")
    @classmethod
    def validate_optional_rarity(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_character_rarity_value(value)

    @field_validator("img_url", mode="before")
    @classmethod
    def validate_img_url(cls, value: Any) -> str | None:
        return _validate_url(value, "Image URL", schemes=IMAGE_URL_SCHEMES)

    @model_validator(mode="after")
    def validate_has_edit(self):
        if not any((self.name, self.anime, self.rarity, self.img_url)):
            raise ValueError("Provide at least one character field to edit")
        return self


class PetUploadPayload(MediaUploadPayload):
    name: str = Field(..., min_length=1, max_length=120)
    petid: Optional[str] = Field(default=None, max_length=80)
    rarity: str = Field(default="Common", max_length=80)
    hp: int = Field(default=100, ge=1, le=9999)
    atk: int = Field(default=20, ge=1, le=9999)
    spd: int = Field(default=20, ge=1, le=9999)
    luck: float | str = 0.08
    ability: str = Field(default="None", max_length=120)
    desc: str = Field(default="", max_length=400)
    zenith_price: int = Field(default=0, ge=0, le=1_000_000)
    req_level: int = Field(default=0, ge=0, le=10_000)
    sort_order: int = Field(default=100, ge=-10_000, le=1_000_000)
    enabled: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def validate_pet_name(cls, value: Any) -> str:
        return _clean_text(value, "Pet name")

    @field_validator("petid", mode="before")
    @classmethod
    def validate_petid(cls, value: Any) -> str | None:
        text = _clean_optional_text(value, "Pet ID")
        if text is None:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", text):
            raise ValueError("Pet ID may only contain letters, numbers, dashes, and underscores")
        return text

    @field_validator("rarity", mode="before")
    @classmethod
    def validate_pet_rarity(cls, value: Any) -> str:
        return _clean_text(value or "Common", "Pet rarity")

    @field_validator("ability", mode="before")
    @classmethod
    def validate_pet_ability(cls, value: Any) -> str:
        return _clean_text(value or "None", "Pet ability")

    @field_validator("desc", mode="before")
    @classmethod
    def validate_pet_desc(cls, value: Any) -> str:
        return _clean_text(value, "Pet description", allow_blank=True)

    @field_validator("luck", mode="before")
    @classmethod
    def validate_pet_luck(cls, value: Any) -> float:
        try:
            return parse_luck(value)
        except UploadError as exc:
            raise ValueError(str(exc)) from exc


async def _get_uploader(user_id: int) -> dict:
    user = await user_collection.find_one(get_user_id_query(user_id)) or {}
    return {
        "id": int(user_id),
        "first_name": user.get("first_name") or user.get("username") or f"User {user_id}",
    }


def _normalize_character_rarity(value: int | str | None) -> str | None:
    if value is None:
        return None
    try:
        return _normalize_character_rarity_value(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _character_response(character: dict) -> dict:
    cleaned = dict(character)
    if cleaned.get("_id") is not None:
        cleaned["_id"] = str(cleaned["_id"])
    return cleaned


@router.get("/admin/upload/options")
async def get_upload_options(user_id: int = Depends(require_uploader_user)):
    return {
        "max_size_mb": 10,
        "role": get_role_payload(user_id),
        "character_rarities": [
            {"value": key, "label": label}
            for key, label in sorted(RARITY_MAP.items())
        ],
        "pet_defaults": {
            "rarity": "Common",
            "hp": 100,
            "atk": 20,
            "spd": 20,
            "luck": 0.08,
            "ability": "None",
            "zenith_price": 0,
            "req_level": 0,
            "sort_order": 100,
            "enabled": True,
        },
    }


@router.patch("/admin/character/{char_id}")
async def edit_character_api(
    char_id: Annotated[str, Path(min_length=1, max_length=80, pattern=CHAR_ID_PATTERN)],
    payload: CharacterEditPayload,
    user_id: int = Depends(require_sudo_user),
):
    character = await collection.find_one({"id": char_id})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    updates: dict[str, str] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.anime is not None:
        updates["anime"] = payload.anime
    if payload.rarity is not None:
        updates["rarity"] = _normalize_character_rarity(payload.rarity)
    if payload.img_url is not None:
        updates["img_url"] = payload.img_url

    updates = {
        key: value
        for key, value in updates.items()
        if value != character.get(key)
    }
    if not updates:
        return {
            "status": "unchanged",
            "message": "No character info changed.",
            "character": _character_response(character),
        }

    result = await collection.update_one({"id": char_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")

    embedded_updates = {
        f"characters.$[character].{key}": value
        for key, value in updates.items()
        if key in {"name", "anime", "rarity", "img_url"}
    }
    if embedded_updates:
        await user_collection.update_many(
            {"characters.id": char_id},
            {"$set": embedded_updates, "$inc": {"version": 1}},
            array_filters=[{"character.id": char_id}],
        )

    if character.get("rarity"):
        invalidate_character_cache(character.get("rarity"))
    if "rarity" in updates:
        invalidate_character_cache(updates["rarity"])

    updated = await collection.find_one({"id": char_id}) or {**character, **updates}
    return {
        "status": "success",
        "message": f"Updated {updated.get('name', char_id)}.",
        "character": _character_response(updated),
    }


@router.post("/admin/upload/character")
async def upload_character_api(
    payload: CharacterUploadPayload,
    user_id: int = Depends(require_uploader_user),
):
    temp_path = None
    try:
        uploader = await _get_uploader(user_id)
        temp_path = await materialize_media_input(
            media_url=payload.media_url,
            media_data=payload.media_data,
            filename=payload.filename,
            temp_prefix=f"web_char_{user_id}",
        )
        character = await upload_character_from_path(
            temp_path,
            name=payload.name,
            anime=payload.anime,
            rarity=payload.rarity,
            added_by_id=uploader["id"],
            added_by_name=uploader["first_name"],
        )
        reward = await grant_upload_reward(user_id, source="web_character")
        reward_text = format_upload_reward(reward)
        message = f"Uploaded {character['name']} ({character['id']})"
        if reward_text:
            message = f"{message}. Reward: {reward_text}"
        return {
            "status": "success",
            "message": message,
            "character": character,
            "reward": reward,
        }
    except UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.exception("Web character upload failed")
        raise HTTPException(status_code=500, detail="Character upload failed") from exc
    finally:
        remove_temp_file(temp_path)


@router.post("/admin/upload/pet")
async def upload_pet_api(
    payload: PetUploadPayload,
    user_id: int = Depends(require_uploader_user),
):
    temp_path = None
    try:
        temp_path = await materialize_media_input(
            media_url=payload.media_url,
            media_data=payload.media_data,
            filename=payload.filename,
            temp_prefix=f"web_pet_{user_id}",
        )
        pet = await upload_pet_from_path(
            temp_path,
            name=payload.name,
            petid=payload.petid,
            rarity=payload.rarity,
            hp=payload.hp,
            atk=payload.atk,
            spd=payload.spd,
            luck=payload.luck,
            ability=payload.ability,
            desc=payload.desc,
            zenith_price=payload.zenith_price,
            req_level=payload.req_level,
            sort_order=payload.sort_order,
            enabled=payload.enabled,
            uploaded_by=user_id,
        )
        reward = await grant_upload_reward(user_id, source="web_pet")
        reward_text = format_upload_reward(reward)
        message = f"Uploaded {pet['name']} ({pet['petid']})"
        if reward_text:
            message = f"{message}. Reward: {reward_text}"
        return {
            "status": "success",
            "message": message,
            "pet": pet,
            "reward": reward,
        }
    except UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.exception("Web pet upload failed")
        raise HTTPException(status_code=500, detail="Pet upload failed") from exc
    finally:
        remove_temp_file(temp_path)
