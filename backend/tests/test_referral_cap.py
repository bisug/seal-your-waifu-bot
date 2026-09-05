"""Referral anti-sybil: lifetime payout cap regression.

Run: cd backend && .venv/bin/python -m pytest tests/test_referral_cap.py -q
"""

import asyncio
from unittest.mock import AsyncMock, patch

import backend.core.referrals as referrals_mod


class _UpdateResult:
    def __init__(self, matched_count=0, modified_count=0, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


def _run_claim(referrer_doc):
    """Run claim_referral_bonus with a mocked DB. Returns (result, update_calls)."""
    with patch.object(referrals_mod, "user_collection") as uc:
        uc.find_one = AsyncMock(return_value=referrer_doc)
        uc.update_one = AsyncMock(side_effect=[_UpdateResult(1, 1), _UpdateResult(1, 1)])
        with (
            patch.object(referrals_mod, "invalidate_user_cache", new=AsyncMock()),
            patch.object(referrals_mod, "add_xp", new=AsyncMock()),
            patch.object(referrals_mod, "check_achievements", new=AsyncMock()),
        ):
            result = asyncio.run(
                referrals_mod.claim_referral_bonus(
                    user_id=111,
                    referrer_id=222,
                    is_new_user=True,
                    first_name="Alt",
                    username="alt_farm",
                )
            )
            return result, uc.update_one


def test_referrer_at_cap_gets_no_payout():
    """Referrer at MAX_REFERRAL_PAYOUTS: claim rejected before any DB write."""
    referrer = {"id": 222, "referrals_count": referrals_mod.MAX_REFERRAL_PAYOUTS}
    result, update_one = _run_claim(referrer)
    assert result.status == "referrer_capped"
    assert not result.applied
    # No writes at all — neither the referred claim nor the payout.
    update_one.assert_not_called()


def test_referrer_below_cap_gets_paid_with_atomic_guard():
    """Referrer below cap: payout update carries the atomic $lt/$exists cap guard."""
    referrer = {"id": 222, "referrals_count": 3}
    result, update_one = _run_claim(referrer)
    assert result.applied
    assert update_one.call_count == 2
    payout_filter = update_one.call_args_list[1].args[0]
    cap_clause = payout_filter["$or"]
    assert {"referrals_count": {"$lt": referrals_mod.MAX_REFERRAL_PAYOUTS}} in cap_clause
    # $exists False keeps legacy referrer docs (no counter yet) eligible.
    assert {"referrals_count": {"$exists": False}} in cap_clause
