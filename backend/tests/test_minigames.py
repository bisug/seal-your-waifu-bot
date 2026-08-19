import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from backend.core.minigames import get_user_energy, consume_energy, MAX_ENERGY, RECHARGE_MINUTES

@pytest.mark.asyncio
async def test_energy_recharge():
    user_id = 12345
    # Energy at 0, last recharge 40 minutes ago (should gain 2 energy)
    last_recharge = datetime.now(timezone.utc) - timedelta(minutes=40)
    user_data = {
        "energy": 0,
        "last_energy_recharge": last_recharge
    }

    with patch("backend.core.minigames.user_collection.update_one", AsyncMock()) as mock_update:
        with patch("backend.core.minigames.invalidate_user_cache", AsyncMock()):
            energy, new_recharge = await get_user_energy(user_id, user_data)
            assert energy == 2
            mock_update.assert_called()

            # Verify update_one was called with correct new energy
            args, kwargs = mock_update.call_args
            # update_one(filter, update, ...)
            update = args[1] if len(args) > 1 else kwargs.get('update')
            assert update["$set"]["energy"] == 2

@pytest.mark.asyncio
async def test_consume_energy_success():
    user_id = 12345
    user_data = {
        "energy": 5,
        "last_energy_recharge": datetime.now(timezone.utc)
    }

    # We need to patch get_user_energy or the find_one inside it
    with patch("backend.core.minigames.user_collection.find_one", AsyncMock(return_value=user_data)):
        with patch("backend.core.minigames.user_collection.update_one", AsyncMock()) as mock_update:
            with patch("backend.core.minigames.invalidate_user_cache", AsyncMock()):
                success = await consume_energy(user_id)
                assert success is True
                mock_update.assert_called()

                # Verify decrement
                args, kwargs = mock_update.call_args
                update = args[1] if len(args) > 1 else kwargs.get('update')
                assert update["$inc"]["energy"] == -1

@pytest.mark.asyncio
async def test_consume_energy_failure():
    user_id = 12345
    user_data = {
        "energy": 0,
        "last_energy_recharge": datetime.now(timezone.utc)
    }

    with patch("backend.core.minigames.user_collection.find_one", AsyncMock(return_value=user_data)):
        with patch("backend.core.minigames.user_collection.update_one", AsyncMock()) as mock_update:
            success = await consume_energy(user_id)
            assert success is False
            mock_update.assert_not_called()
