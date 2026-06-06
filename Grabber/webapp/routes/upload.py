from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from Grabber import LOGGER
from Grabber.core.uploads import (
    UploadError,
    materialize_media_input,
    remove_temp_file,
    upload_character_from_path,
    upload_pet_from_path,
)
from Grabber.core.utils import get_user_id_query
from Grabber.database import user_collection
from Grabber.modules.collection.rarities import RARITY_MAP
from Grabber.webapp.auth import require_sudo_user

router = APIRouter()


class MediaUploadPayload(BaseModel):
    media_url: Optional[str] = None
    media_data: Optional[str] = None
    filename: Optional[str] = None


class CharacterUploadPayload(MediaUploadPayload):
    name: str = Field(..., min_length=1, max_length=120)
    anime: str = Field(..., min_length=1, max_length=120)
    rarity: int | str


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


async def _get_uploader(user_id: int) -> dict:
    user = await user_collection.find_one(get_user_id_query(user_id)) or {}
    return {
        "id": int(user_id),
        "first_name": user.get("first_name") or user.get("username") or f"User {user_id}",
    }


@router.get("/admin/upload/options")
async def get_upload_options(user_id: int = Depends(require_sudo_user)):
    return {
        "max_size_mb": 10,
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


@router.post("/admin/upload/character")
async def upload_character_api(
    payload: CharacterUploadPayload,
    user_id: int = Depends(require_sudo_user),
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
        return {
            "status": "success",
            "message": f"Uploaded {character['name']} ({character['id']})",
            "character": character,
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
    user_id: int = Depends(require_sudo_user),
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
        return {
            "status": "success",
            "message": f"Uploaded {pet['name']} ({pet['petid']})",
            "pet": pet,
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
