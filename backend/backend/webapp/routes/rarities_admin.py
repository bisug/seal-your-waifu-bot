from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.core.logging import get_logger
from backend.core.rarities import (
    EDITABLE_FIELDS,
    NUMERIC_FIELDS,
    RARITY_MAP,
    add_rarity,
    get_rarity_docs,
    rename_rarity,
    set_rarity_field,
)
from backend.webapp.auth import require_sudo_user

LOGGER = get_logger(__name__)

router = APIRouter()


class RarityAddRequest(BaseModel):
    rarity_id: int = Field(..., ge=1, le=9999)
    emoji: str = Field(..., min_length=1, max_length=16)
    name: str = Field(..., min_length=1, max_length=40)


class RarityFieldRequest(BaseModel):
    field: str
    value: int | str


class RarityRenameRequest(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=16)
    name: str = Field(..., min_length=1, max_length=40)


@router.get("/admin/rarities")
async def list_rarities(user_id: int = Depends(require_sudo_user)):
    """Full rarity config for the admin editor."""
    return {"rarities": get_rarity_docs(), "fields": sorted(EDITABLE_FIELDS)}


@router.post("/admin/rarities")
async def create_rarity(payload: RarityAddRequest, user_id: int = Depends(require_sudo_user)):
    error = await add_rarity(payload.rarity_id, payload.emoji.strip(), payload.name.strip())
    if error:
        raise HTTPException(status_code=400, detail=error)
    LOGGER.info("Rarity %s added by user %s", payload.rarity_id, user_id)
    return {"status": "success", "rarity_id": payload.rarity_id}


@router.patch("/admin/rarities/{rarity_id}")
async def update_rarity(
    rarity_id: int,
    payload: RarityFieldRequest,
    user_id: int = Depends(require_sudo_user),
):
    if payload.field not in EDITABLE_FIELDS:
        raise HTTPException(
            status_code=400, detail=f"Unknown field. Valid: {', '.join(sorted(EDITABLE_FIELDS))}"
        )
    if payload.field in NUMERIC_FIELDS:
        if not isinstance(payload.value, int) or payload.value < 0:
            raise HTTPException(status_code=400, detail="Value must be a non-negative integer")
        value: int | str = payload.value
    else:
        value = str(payload.value).strip()
        if not value:
            raise HTTPException(status_code=400, detail="Value cannot be empty")

    changed = await set_rarity_field(rarity_id, payload.field, value)
    if not changed:
        raise HTTPException(status_code=400, detail="No change (value already set or rarity missing)")
    LOGGER.info("Rarity %s field %s updated by user %s", rarity_id, payload.field, user_id)
    return {"status": "success", "rarity_id": rarity_id, "field": payload.field, "value": value}


@router.post("/admin/rarities/{rarity_id}/rename")
async def rename_rarity_api(
    rarity_id: int,
    payload: RarityRenameRequest,
    user_id: int = Depends(require_sudo_user),
):
    result = await rename_rarity(rarity_id, payload.emoji.strip(), payload.name.strip())
    if not result:
        raise HTTPException(status_code=404, detail="Rarity not found")
    old_label, new_label = result
    LOGGER.info("Rarity %s renamed %s -> %s by user %s", rarity_id, old_label, new_label, user_id)
    return {"status": "success", "old_label": old_label, "new_label": new_label}


@router.delete("/admin/rarities/{rarity_id}")
async def delete_rarity_api(rarity_id: int, user_id: int = Depends(require_sudo_user)):
    if rarity_id not in RARITY_MAP:
        raise HTTPException(status_code=404, detail="Rarity not found")

    from backend.database import collection, rarities_collection
    label = RARITY_MAP[rarity_id]

    # Block deletion while characters still use the rarity — deleting would
    # orphan their docs (spawn/claim/shop lookups would fail on the label).
    in_use = await collection.count_documents({"rarity": label})
    if in_use > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {in_use} character(s) still use {label}. Re-assign them first.",
        )

    await rarities_collection.delete_one({"_id": rarity_id})
    from backend.core.rarities import refresh_rarities
    await refresh_rarities()
    LOGGER.info("Rarity %s (%s) deleted by user %s", rarity_id, label, user_id)
    return {"status": "success", "deleted": label}
