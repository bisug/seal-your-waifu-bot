# Pokémon Migration — Task Plan

> Update task states as work progresses. One `in-progress` at a time.
> Phases are sequential; tasks within a phase can be reordered.

## Phase 0 — Setup

- [x] Create `dev` branch from `main` @ `ee6f247`
- [x] Create `docs/dev/` tracking docs (CONTEXT, PLAN, CHANGELOG)

## Phase 1 — Remove pets (backend)

- [x] 1.1 Delete `core/pets.py` + `modules/progression/pet.py`
- [x] 1.2 Rewire `core/eggs.py` — drop Caregiver incubation bonus (flat wait times)
- [x] 1.3 Rewire `modules/games/battle.py` — remove pet combat stats (base stats only)
- [x] 1.4 Rewire `core/referrals.py` — replace reward pet with shards/zenith reward
- [x] 1.5 Remove pet endpoints: `webapp/routes/shop.py` (`/shop/pets`),
      `users.py` (`current_pet`, pets in `/me`), `staff.py`, `upload.py`,
      `progression.py` pet bits
- [x] 1.6 Remove pet refs from `core/user.py`, `uploads.py`, `startup.py`,
      `client.py`, `runner.py`, `modules/info/{privacy,profile,start}.py`,
      `modules/economy/{shop,hunt}.py`, `modules/admin/upload.py`,
      `modules/social/referral.py`, `webapp/schemas.py`
- [x] 1.7 Drop `pet_catalog` collection + indexes from `database/__init__.py`
- [x] 1.8 Delete `tests/test_pets.py`; fix remaining tests
- [x] 1.9 Validate: pytest green (48 passed), compileall clean, ruff F401/F811/F841 clean

## Phase 2 — Remove pets (frontend)

- [x] 2.1 Delete `pages/MyPets.tsx`, `pages/PetShop.tsx`, `components/pet/`
- [x] 2.2 Remove pet routes/nav/types from `App.tsx`, `NavigationDrawer.tsx`,
      `types.d.ts`, api client
- [x] 2.3 Validate: lint + type-check + build green

## Phase 3 — Pokémon backend

- [x] 3.1 Add `pokemon_catalog` collection + indexes to `database/__init__.py`
- [x] 3.2 Write `scripts/pokemon_import.py` — fetch from PokéAPI, map fields
      (dex#, name, type, sprite, rarity by base-stat total, sort by dex),
      insert to `pokemon_catalog`; idempotent
- [x] 3.3 Run import against Atlas — 1025 Pokémon imported, Pikachu verified
- [x] 3.4 Create `core/pokemon.py` — engine: list, find, ensure_user_state,
      active pokemon, rarity tiers
- [x] 3.5 Bot commands: `modules/progression/pokemon.py` (/starter, /mypokemon,
      /setpokemon, /pokedex); battle.py wired to active Pokémon stats
- [x] 3.6 WebApp endpoints: `/shop/pokemon` catalog browse, `/me` pokemon block
- [x] 3.7 Tests: `tests/test_pokemon.py` (8 tests: normalize, find, grant guard,
      active, XP level-up, battle stats)
- [x] 3.8 Validate: pytest green (56 passed), compileall clean, ruff clean

## Phase 4 — Pokémon frontend

- [x] 4.1 `pages/MyPokemon.tsx` + `pages/Pokedex.tsx` + `components/pokemon/PokemonCard.tsx`
- [x] 4.2 Wire routes/nav/types (tabs `mypokemon`/`pokedex`, aliases, nav items, UserContext Pokemon interface)
- [x] 4.3 Validate: lint + type-check + build green
- [x] 4.4 Browser-verify via preview server (stubbed telegram + API: pages render,
      rarity filter, load-more, set-active flow, nav items present)
- [x] 4.5 Remove rarity concept — organize by Pokémon type instead:
      import script, core normalize, DB index (rarity→types), shop `type` filter,
      schemas, bot commands (type emoji badges), tests, frontend (Pokedex type
      filter, PokemonCard type emojis, UserContext interface); Atlas `$unset`
      rarity from 1025 catalog docs

## Phase 5 — Integration + migration

- [ ] 5.1 Full-stack smoke test (bot commands + WebApp flows)
- [ ] 5.2 Data migration script: strip `pets`/`current_pet` from user docs,
      gift starter Pokémon; drop `pet_catalog` collection in Atlas
- [ ] 5.3 Update README (feature list, structure tree)
- [ ] 5.4 Final validation: backend tests + frontend build
- [ ] 5.5 Merge `dev` → `main`, push

## Blockers / Notes

- (none yet)
