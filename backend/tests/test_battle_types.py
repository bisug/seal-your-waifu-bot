"""Battle type-effectiveness regression: chart lookups and damage integration.

Run: cd backend && uv run python -m pytest tests/test_battle_types.py -q
"""

from backend.modules.games.battle import (
    FALLBACK_STATS,
    effectiveness_text,
    simulate_battle,
    type_multiplier,
)


def test_type_multiplier_super_effective():
    assert type_multiplier(["fire"], ["grass"]) == 2.0
    assert type_multiplier(["water"], ["ground", "rock"]) == 4.0


def test_type_multiplier_resisted():
    assert type_multiplier(["fire"], ["fire"]) == 0.5
    assert type_multiplier(["grass"], ["poison", "bug"]) == 0.25


def test_type_multiplier_immune():
    assert type_multiplier(["electric"], ["ground"]) == 0.0
    assert type_multiplier(["normal"], ["ghost"]) == 0.0


def test_type_multiplier_dual_attacker():
    # Water/flying vs grass: 0.5 * 2 = 1.0
    assert type_multiplier(["water", "flying"], ["grass"]) == 1.0


def test_type_multiplier_empty_types_neutral():
    assert type_multiplier([], ["fire"]) == 1.0
    assert type_multiplier(["fire"], []) == 1.0
    assert type_multiplier(None, None) == 1.0


def test_effectiveness_text():
    assert "no effect" in effectiveness_text(0.0)
    assert "Super effective" in effectiveness_text(2.0)
    assert "Not very effective" in effectiveness_text(0.5)
    assert effectiveness_text(1.0) == ""


def test_simulate_battle_immune_deals_zero():
    """Electric vs pure Ground: every hit is 0 — battle runs, no crash."""
    p1 = {**FALLBACK_STATS, "name": "Pikachu", "types": ["electric"], "spd": 100}
    p2 = {**FALLBACK_STATS, "name": "Diglett", "types": ["ground"], "spd": 50}
    winner, log = simulate_battle(p1.copy(), p2.copy(), "Pikachu", "Diglett")
    assert winner in (1, 2)
    assert "passed right through" in log


def test_simulate_battle_returns_winner_and_log():
    p1 = {**FALLBACK_STATS, "name": "A", "types": ["fire"]}
    p2 = {**FALLBACK_STATS, "name": "B", "types": ["grass"], "hp": 20, "max_hp": 20}
    winner, log = simulate_battle(p1.copy(), p2.copy(), "A", "B")
    assert winner == 1  # fire vs grass: super effective, B folds fast
    assert "Super effective" in log
