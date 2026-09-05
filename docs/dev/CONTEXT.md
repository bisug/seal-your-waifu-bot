# Pokémon Migration — Context

> Living context doc. Read this first when resuming work on the migration.
> Branch: `dev` (forked from `main` @ `ee6f247`). Merge to `main` only after all tasks complete.

## Decision (2026-09-05)

Replace the pets system with Pokémon sourced from PokéAPI.

- **Approach**: full removal of pets, then Pokémon integration built on the same
  generic engine patterns (catalog + user-owned creatures + active creature).
- **Branch**: `dev` — all work happens here; `main` stays deployable.
- **Data**: existing user pets are removed (user decision); users get a fresh start.
  Migration of user data happens only after integration is verified.

## Why the pet engine is reusable

`pet_catalog` is a generic creature system. Pokémon maps 1:1:

| Pet field | Pokémon equivalent |
|---|---|
| `petid` | Pokédex number |
| `name` | Pokémon name |
| `ability` | Primary type |
| `img` | Sprite URL (official artwork) |
| `rarity` | Derived from base-stat total |
| `sort_order` | Dex order |

PokéAPI (https://pokeapi.co) is free, no key. Hit it **only at import time**
(one-time script → `pokemon_catalog` collection). No runtime dependency.

## Known risks

1. **Nintendo IP** — sprites are aggressively enforced. Higher risk than anime
   waifus. DMCA flow (`modules/info/dmca.py`) already exists as mitigation.
2. **Coupled systems** — pets touch ~24 backend files: eggs (Caregiver incubation
   bonus), battle (pet combat stats), referrals (reward pet), shop, uploads,
   staff, profile, GDPR deletion, WebApp routes. All must be decoupled or
   rewired to Pokémon equivalents.

## Key files (pets, to remove/rewire)

- `backend/backend/core/pets.py` (498 lines, 22 funcs) — engine
- `backend/backend/modules/progression/pet.py` (325) — bot commands
- `backend/backend/core/eggs.py` — imports `get_caregiver_incubation_minutes`
- `backend/backend/modules/games/battle.py` — imports `get_active_pet`, pet stats
- `backend/backend/core/referrals.py` — reward pet on referral
- `backend/backend/webapp/routes/shop.py` — `/shop/pets` endpoint
- `backend/backend/webapp/routes/users.py` — `current_pet`, pet list in `/me`
- `backend/backend/webapp/routes/staff.py`, `upload.py`, `progression.py`
- `backend/backend/core/uploads.py`, `user.py`, `startup.py`, `client.py`, `runner.py`
- `backend/backend/database/__init__.py` — `pet_catalog` collection + 3 indexes
- Frontend: `pages/MyPets.tsx` (412), `pages/PetShop.tsx` (263),
  `components/pet/PetActionModal.tsx` (304), plus nav/routes/types
- Tests: `tests/test_pets.py` (18 refs)

## Working conventions

- Update `PLAN.md` (task states) and `CHANGELOG.md` (what changed) as work lands.
- Validate after each task: `cd backend && uv run python -m pytest tests/ -q`
  and `cd frontend && bun run lint && bun run type-check && bun run build`.
- Frontend preview: port 4173 (`bun run preview`), stub `**/telegram-web-app.js`
  route before browser tests (telegram.org is network-blocked locally).
