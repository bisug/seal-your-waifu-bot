# Pokémon Migration — Changelog

> Newest first. One entry per meaningful change. Reference task IDs from PLAN.md.

## 2026-09-05

- **[1.1–1.9]** Phase 1 complete — pets fully removed from backend:
  - Deleted `core/pets.py` (498 lines), `modules/progression/pet.py` (325 lines),
    `tests/test_pets.py`.
  - `battle.py`: flat base stats for all fighters (Pokémon stats arrive Phase 3).
  - `eggs.py`/`hunt.py`/`progression.py`: flat incubation waits, no pet luck;
    hunt cooldown flat 60s; egg drop chance from pass multiplier only.
  - `referrals.py`: referred reward pet → shards-only (1500→2500 to compensate).
  - WebApp: removed `/shop/pets`, `/shop/buy/pet`, `/admin/upload/pet`,
    `/pets/set_active`, `/pets/feed`, `/pets/train`; `/me` no longer returns
    `current_pet`/`pets`; staff contributions character-only.
  - `database/__init__.py`: `pet_catalog` collection + 3 indexes dropped.
  - Bot commands: `/mypet`, `/petshop`, `/feed`, `/train` removed from help
    and command list; `/hunt` reworded to "Hunt for eggs".
  - Tests: 48 passed (was 54; pet tests removed, hunt/referral tests updated).
    compileall + ruff F401/F811/F841 clean.
- **[0.1, 0.2]** Created `dev` branch from `main` @ `ee6f247`.
  Added `docs/dev/CONTEXT.md`, `PLAN.md`, `CHANGELOG.md` to track the
  pets→Pokémon migration. No code changes yet.
