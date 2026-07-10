from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from Grabber.webapp.auth import get_current_user
from Grabber.core.minigames import get_user_energy, consume_energy, reward_minigame, validate_session, MAX_ENERGY

router = APIRouter()

class GameSubmitRequest(BaseModel):
    game_type: str
    score: int = 0

@router.get("/minigames/state")
async def get_minigames_state(user_id: int = Depends(get_current_user)):
    energy, last_recharge = await get_user_energy(user_id)
    return {
        "energy": energy,
        "max_energy": MAX_ENERGY,
        "last_energy_recharge": last_recharge.isoformat() if last_recharge else None
    }

@router.post("/minigames/start/{game_type}")
async def start_minigame(game_type: str, user_id: int = Depends(get_current_user)):
    if game_type not in ["cipher_match", "nexus_wheel"]:
        raise HTTPException(status_code=400, detail="Invalid game type")

    success = await consume_energy(user_id, game_type)
    if not success:
        raise HTTPException(status_code=400, detail="Not enough energy")

    return {"status": "success"}

@router.post("/minigames/submit")
async def submit_minigame(
    request: GameSubmitRequest,
    user_id: int = Depends(get_current_user)
):
    game_type = request.game_type
    score = request.score

    if game_type not in ["cipher_match", "nexus_wheel"]:
        raise HTTPException(status_code=400, detail="Invalid game type")

    time_taken = await validate_session(user_id, game_type)
    if time_taken is None:
        raise HTTPException(status_code=403, detail="No active session for this game. Did you start it?")

    rewards = await reward_minigame(user_id, game_type, score, time_taken)

    if "error" in rewards:
        raise HTTPException(status_code=400, detail=rewards["error"])

    return {
        "status": "success",
        "rewards": rewards
    }
