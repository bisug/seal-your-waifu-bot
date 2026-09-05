# Pokémon Migration — Changelog

> Newest first. One entry per meaningful change. Reference task IDs from PLAN.md.

## 2026-09-05

- **[3.1–3.8]** Phase 3 complete — Pokémon backend live:
  - `database/__init__.py`: `pokemon_catalog` collection + 3 indexes
    (unique dex, enabled+sort_order, rarity).
  - `scripts/pokemon_import.py`: one-time PokéAPI import (Gen 1-9, dex 1-1025),
    rarity by base-stat total (Legendary ≥600, Mythic ≥540, Epic ≥480, Rare ≥410,
    Common below), official artwork, idempotent upserts. **1025 imported to Atlas**,
    Pikachu spot-checked.
  - `core/pokemon.py` engine: normalize/merge catalog+owned, ensure user state
    ($set only missing fields), find/grant (atomic $ne dup guard), set active,
    add XP with level-up loop, battle_stats (level-scaled).
  - `modules/progression/pokemon.py`: `/starter` (5 starters, atomic claim),
    `/mypokemon`, `/setpokemon`, `/pokedex`.
  - `battle.py`: fighters now use active Pokémon stats (Fists fallback).
  - WebApp: `/shop/pokemon` paged catalog browse (rarity filter);
    `/me` returns `pokemon[]` + `current_pokemon` (catalog fetched by owned
    dexes only — no full-catalog scan).
  - Tests: `tests/test_pokemon.py` (8). Suite: 56 passed, compileall + ruff clean.
- **[2.1–2.3]** Phase 2 complete — pets fully removed from frontend:
  - Deleted `pages/MyPets.tsx`, `pages/PetShop.tsx`, `components/pet/PetActionModal.tsx`.
  - `App.tsx`: pet tabs/aliases/routes/modal state removed.
  - `NavigationDrawer`: Companions nav item removed.
  - `UserContext`: `Pet` interface + `current_pet`/`pets` fields dropped.
  - `Profile`: companion card removed; `Referrals`: pet reward text → coins-only;
    `Staff`: pet uploads removed; `Upload`: character-only mode;
    `Hatchery`: copy tweak.
  - Validate: biome lint (4 pre-existing warnings), tsc clean, vite build ✓.
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
