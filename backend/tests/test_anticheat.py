"""Guards for the minigame anti-cheat fixes.

1. reward_minigame must clamp client-supplied scores to the real maximum
   (8 pairs) so forged scores cannot mint unbounded shards/XP.
2. validate_session must return None (not a fabricated session) when Redis
   is unavailable, otherwise rewards are grantable without starting a game.
"""
import pytest
from unittest.mock import AsyncMock, patch

from backend.core import minigames


@pytest.mark.asyncio
async def test_cipher_match_score_is_clamped():
    # A forged score of 1_000_000 must be capped at 8 pairs:
    # max reward = 8*25 + 100 (bonus rand) + 100 (speed bonus) = 400 shards.
    with patch.object(minigames.user_collection, "update_one", AsyncMock()) as mock_update:
        with patch.object(minigames, "add_xp", AsyncMock()):
            with patch.object(minigames, "invalidate_user_cache", AsyncMock()):
                session = {"start_time": minigames.get_now_utc().timestamp() - 30}
                result = await minigames.reward_minigame(1, "cipher_match", score=1_000_000, session_data=session)

    assert "error" not in result
    assert result["shards"] <= 8 * 25 + 100 + 100
    args, _ = mock_update.call_args
    assert args[1]["$inc"]["balance"] == result["shards"]


@pytest.mark.asyncio
async def test_validate_session_refuses_without_redis():
    with patch.object(minigames, "r", None):
        session = await minigames.validate_session(1, "cipher_match")
    assert session is None
