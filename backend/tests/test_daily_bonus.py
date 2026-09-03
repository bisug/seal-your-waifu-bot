"""Daily bonus roll: reward shape + once-per-day guard.

Run: cd backend && .venv/bin/python -m pytest tests/test_daily_bonus.py -q
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import backend.modules.info.start as start_mod


class _UpdateResult:
    def __init__(self, modified_count, upserted_id):
        self.modified_count = modified_count
        self.upserted_id = upserted_id


def _fake_message():
    msg = MagicMock()
    msg.from_user.id = 42
    msg.from_user.first_name = "Tester"
    msg.reply_text = AsyncMock()
    return msg


def _run(param="bonus"):
    msg = _fake_message()
    with (
        patch.object(start_mod, "user_collection") as uc,
        patch.object(start_mod, "invalidate_user_cache", new=AsyncMock()),
        patch.object(start_mod, "reply_media_dynamic", new=AsyncMock()),
        patch.object(start_mod, "sample_character_by_rarity", new=AsyncMock(return_value=None)),
    ):
        uc.update_one = AsyncMock(return_value=_UpdateResult(1, None))
        asyncio.run(start_mod._handle_bonus_param(msg))
        return msg, uc.update_one


def test_bonus_claim_is_atomic_and_daily():
    """Claim writes last_bonus_date with a $ne guard -> once per day."""
    msg, update_one = _run()
    filter_doc = update_one.call_args[0][0]
    assert isinstance(filter_doc["last_bonus_date"], dict)
    assert "$ne" in filter_doc["last_bonus_date"]
    # $set carries today's date into the same atomic update
    update_doc = update_one.call_args[0][1]
    assert update_doc["$set"]["last_bonus_date"] == filter_doc["last_bonus_date"]["$ne"]


def test_bonus_already_claimed_short_circuits():
    """Second claim same day: no reward ops, 'already claimed' reply."""
    msg = _fake_message()
    with (
        patch.object(start_mod, "user_collection") as uc,
        patch.object(start_mod, "invalidate_user_cache", new=AsyncMock()),
        patch.object(start_mod, "reply_media_dynamic", new=AsyncMock()),
    ):
        uc.update_one = AsyncMock(return_value=_UpdateResult(0, None))
        asyncio.run(start_mod._handle_bonus_param(msg))
        filter_doc = uc.update_one.call_args[0][0]
        # The $ne guard is what makes a losing claim a no-op in the DB.
        assert isinstance(filter_doc["last_bonus_date"], dict)
        assert "$ne" in filter_doc["last_bonus_date"]
        assert "bonus" in msg.reply_text.call_args[0][0].lower()


def test_bonus_reward_distribution_covers_all_kinds():
    """Over many rolls, egg/character/coins branches all fire and shapes are valid."""
    kinds = set()
    for seed in range(200):
        with (
            patch.object(start_mod, "user_collection") as uc,
            patch.object(start_mod, "invalidate_user_cache", new=AsyncMock()),
            patch.object(start_mod, "reply_media_dynamic", new=AsyncMock()),
            patch.object(start_mod, "random") as rnd,
        ):
            rnd.random.return_value = 0.10  # egg branch
            uc.update_one = AsyncMock(return_value=_UpdateResult(1, None))
            asyncio.run(start_mod._handle_bonus_param(_fake_message()))
            doc = uc.update_one.call_args[0][1]
            assert doc["$push"]["eggs"]["id"].startswith("egg_")
            kinds.add("egg")
        with (
            patch.object(start_mod, "user_collection") as uc,
            patch.object(start_mod, "invalidate_user_cache", new=AsyncMock()),
            patch.object(start_mod, "reply_media_dynamic", new=AsyncMock()),
            patch.object(start_mod, "random") as rnd,
            patch.object(start_mod, "sample_character_by_rarity", new=AsyncMock(return_value=None)),
        ):
            rnd.random.return_value = 0.50  # character branch, empty pool -> coins fallback
            uc.update_one = AsyncMock(return_value=_UpdateResult(1, None))
            asyncio.run(start_mod._handle_bonus_param(_fake_message()))
            doc = uc.update_one.call_args[0][1]
            assert doc["$inc"]["balance"] == 500
            kinds.add("character_fallback")
        with (
            patch.object(start_mod, "user_collection") as uc,
            patch.object(start_mod, "invalidate_user_cache", new=AsyncMock()),
            patch.object(start_mod, "reply_media_dynamic", new=AsyncMock()),
            patch.object(start_mod, "random") as rnd,
        ):
            rnd.random.return_value = 0.90  # coins branch
            rnd.randint.return_value = 555
            uc.update_one = AsyncMock(return_value=_UpdateResult(1, None))
            asyncio.run(start_mod._handle_bonus_param(_fake_message()))
            doc = uc.update_one.call_args[0][1]
            assert doc["$inc"]["balance"] == 555
            kinds.add("coins")
    assert kinds == {"egg", "character_fallback", "coins"}
