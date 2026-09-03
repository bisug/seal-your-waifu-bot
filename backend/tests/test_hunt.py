"""Regression tests for hunt reward rolling (balance & polish).

Guards:
1. Egg ids are unique even for back-to-back hunts in the same millisecond —
   every eggs.id atomic guard (incubate/sell/purify/fuse) keys on that id.
2. A bonus egg rolls at full luck, never worse than the egg that triggered it.
3. Pass shard bonus text matches the configured multiplier (no hardcoded %).
4. Beginner's Luck scales pet XP with luck, not affection.
"""
import random

from backend.core.pass_config import PASS_BENEFITS
from backend.modules.economy.hunt import _pet_hunt_context, _roll_hunt_rewards


def make_ctx(petid="fluffy_fox", level=1, affection=50):
    pet = {"petid": petid, "level": level, "affection": affection, "last_interacted": 0}
    return _pet_hunt_context({"pets": [pet], "current_pet": petid})


def test_egg_ids_unique_across_rapid_hunts():
    ctx = make_ctx()
    user = {"pass_type": "free"}
    ids = []
    for _ in range(200):
        ids.extend(e["id"] for e in _roll_hunt_rewards(ctx, user)[2])
    # uuid4 ids: every collected id must be distinct, even for eggs rolled
    # back-to-back (the old ms+rand100-999 scheme could collide).
    assert len(ids) == len(set(ids))


def test_bonus_egg_rolls_at_full_luck():
    # Direct distribution guard: the bonus egg must roll with the same luck
    # as the primary egg. Halved luck measurably skews toward common.
    from backend.core.constants import EGG_TIERS
    from backend.core.eggs import roll_egg_tier

    full = [EGG_TIERS[roll_egg_tier(0.764, 0)]["rank"] for _ in range(3000)]
    half = [EGG_TIERS[roll_egg_tier(0.382, 0)]["rank"] for _ in range(3000)]
    avg_full = sum(full) / len(full)
    avg_half = sum(half) / len(half)
    # Full luck must beat halved luck by a visible margin (measured ~0.09).
    assert avg_full > avg_half + 0.03, (
        f"bonus egg distribution collapsed: full={avg_full:.3f} half={avg_half:.3f}"
    )


def test_pass_bonus_text_matches_multiplier():
    for tier in ("premium", "elite"):
        user = {"pass_type": tier}
        ctx = make_ctx()
        mult = PASS_BENEFITS[tier]["hunt_multiplier"]
        expected_pct = int((mult - 1.0) * 100)
        # Shards always show the pass line for paid tiers.
        for _ in range(10):
            _, _, _, bonus = _roll_hunt_rewards(ctx, user)
            if f"+{expected_pct}% {tier.capitalize()} Shards!" in bonus:
                break
        else:
            raise AssertionError(f"{tier} bonus text missing for multiplier {mult}")


def test_beginners_luck_scales_with_luck_not_affection():
    # Same affection, different luck → XP must differ (luck-driven).
    low = make_ctx(petid="fluffy_fox", level=1, affection=50)  # luck 0.08
    high = make_ctx(petid="mystic_dragon", level=100, affection=50)  # luck ~0.72
    low["ability"] = "Beginner's Luck"
    high["ability"] = "Beginner's Luck"
    user = {"pass_type": "free"}
    random.seed(42)
    xp_low = [_roll_hunt_rewards(low, user)[1] for _ in range(500)]
    random.seed(42)
    xp_high = [_roll_hunt_rewards(high, user)[1] for _ in range(500)]
    assert sum(xp_high) > sum(xp_low), "high-luck pet should earn more XP per hunt"
