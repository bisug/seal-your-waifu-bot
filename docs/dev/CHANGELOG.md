# Pokémon Migration — Changelog

> Newest first. One entry per meaningful change. Reference task IDs from PLAN.md.

## 2026-09-05

- **[6.0]** Production hardening — 3 spawn bugs found in audit, fixed:
  - **Doc collision**: Pokémon spawn state now keyed on dedicated
    `_id: pokespawn:{chat_id}` — can no longer overwrite the character-spawn
    doc for the same chat (old filter `{"chat_id", "kind": "pokemon"}` upserted
    the same doc the character system uses).
  - **Permanent block**: unguessed Pokémon spawns expire after 30 min
    (`POKEMON_SPAWN_MAX_AGE_SECONDS`); Mongo fallback reads filter on
    `last_spawn_time`, so a stale spawn never blocks new ones forever.
  - **Unstable trigger**: Pokémon spawn slot now uses a dedicated Redis counter
    (`pokespawn:slot:{chat_id}`) instead of `count % (target_freq * 8)` —
    activity-driven `target_freq` fluctuations (40/60/80) no longer make the
    Pokémon slot un-hittable. In-process fallback counter when Redis is down.
  - Tests updated for `_id`-keyed filters + new expiry/slot-counter tests
    (78 passing).
- **[5.1–5.5]** Phase 5 complete — migration done, merged to main:
  - `scripts/pokemon_migration.py`: stripped pet fields from 99 user docs,
    gifted starters where needed (0 — all pet owners already had Pokémon),
    dropped `pet_catalog` from Atlas. Post-conditions verified.
  - README fully updated: pets → Pokémon across all sections + new
    Pokémon feature section (starters, leveling, evolution thresholds,
    type-effectiveness battles, guess spawns, Pokédex).
  - Final validation: pytest 75, compileall + ruff clean, biome/tsc/build ✓.
  - `dev` merged to `main` and pushed. Migration complete.
- **[4.8]** Guess-the-Pokémon random spawn:
  - New chat minigame: a wild Pokémon spawns as spoilered artwork (random
    enabled catalog pick via `$sample`); users type its name in chat — first
    correct guess claims it. Name matching mirrors nguess (full name or any
    part >2 chars, case-insensitive).
  - State architecture mirrors character spawns exactly: Redis hash
    (`pokespawn:state:{chat_id}`, 1h TTL) with Mongo fallback
    (`kind: "pokemon"` docs in spawns collection); atomic claim via
    Mongo `update_one` guard prevents double-wins.
  - Trigger: every 8th spawn slot in `message_counter` becomes a Pokémon
    spawn (skipped while one is unclaimed in the chat).
  - Rewards: +150 coins, +15 user XP, +25 active-partner XP — partner XP
    can trigger evolution, announced in the win message.
  - Fixed during testing: Redis `hgetall` returns bytes keys — decode
    before the `dex` guard (would have silently always fallen back to Mongo).
  - Tests: 6 new (variants, claim atomicity, Redis bytes round-trip, Mongo
    fallback). 75 passed; compileall + ruff clean.
- **[4.7]** Evolution + battle integration:
  - Evolution engine (`core/pokemon.py`): Pokémon auto-evolve when XP level-ups
    push them past stage-scaled thresholds (`EVOLVE_LEVELS = (16, 32)`).
    Successors resolved from catalog `evolves_from` (exact for branch points —
    Eevee picks a random unowned eeveelution; owned targets skipped so no
    duplicate dexes). `current_pokemon` follows the evolved dex.
    `add_pokemon_xp` now returns `(new_level, evolution_info)`.
  - Battle type effectiveness (`modules/games/battle.py`): full standard 18×18
    `TYPE_CHART` with immunities (electric→ground 0x, normal→ghost 0x, etc.).
    Damage multiplied by the product of attacker-type vs defender-type
    multipliers; log shows Super effective / Not very effective / no-effect
    lines. Immune hits log "passed right through".
  - Battle Pokémon XP: winner's active partner +40 XP, loser's +15 — battles
    now train Pokémon, and evolutions triggered mid-battle are announced in
    the result message.
  - `battle_stats` includes `types` for effectiveness; `FALLBACK_STATS`
    (Fists) stays neutral.
  - Tests: 13 new (evolution threshold/swap/branch/owned-skip, type chart
    lookups, dual-type products, immunity battle, super-effective KO).
    69 passed; compileall + ruff clean.
- **[4.6]** Full PokéAPI feature set implemented:
  - `scripts/pokemon_import.py`: now imports shiny artwork, cry URL,
    height/weight, abilities (with hidden flag), moves (capped at 24), English
    flavor text, growth rate, gender rate, capture rate, base happiness, egg
    groups, evolves_from dex, full evolution chain, legendary/mythical flags,
    generation. Atlas re-imported — 1025 docs, 0 missing fields.
  - `core/pokemon.py` normalize + `schemas.py` PokemonCatalogItem extended with
    all new fields.
  - New endpoint GET `/pokemon/{dex}`: full detail + resolved evolution line
    (name/img/types/owned per stage) + owned flag.
  - Bot `/pokedex`: category, height/weight, abilities, generation, legendary/
    mythical tags, flavor text.
  - New `PokemonDetailModal.tsx`: artwork with shiny toggle, cry playback,
    animated stat bars, profile grid (height/weight/friendship/catch rate),
    abilities, breeding (gender %, egg groups, growth), clickable evolution
    line, moves. Wired into MyPokemon (active card → detail) and Pokedex
    (any card → detail).
  - Refactor to existing libraries (no new deps): Pokedex uses `useInfiniteGrid`
    (react-query infinite scroll, dedupe, cache) instead of manual load-more;
    PokemonDetailModal uses `useApi` (cached detail fetch, auto-cancel) instead
    of manual useState/useEffect fetching.
  - Browser-verified via preview 4173 (stubbed telegram + API): Pokédex grid,
    type filters, infinite scroll, detail modal (stats, abilities, breeding,
    evolution line navigation, moves, shiny/cry buttons), MyPokemon active card.
  - Validate: pytest 56, compileall/ruff clean, biome/tsc/build ✓.
- **[4.5]** Rarity removed from Pokémon — organized by type instead:
  - Rationale: rarity tiers don't fit Pokémon; types are the natural taxonomy.
  - `scripts/pokemon_import.py`: RARITY_TIERS + rarity_for deleted; no rarity
    field in upserts.
  - `core/pokemon.py`: normalize no longer returns rarity.
  - `database/__init__.py`: catalog index rarity → `types`.
  - `/shop/pokemon`: `rarity` query param → `type` (matches on `types`).
  - `schemas.py`: PokemonCatalogItem drops rarity.
  - Bot commands: TYPE_EMOJI badges (18 types) replace rarity badges;
    `/pokedex` shows base-stat total instead of rarity.
  - Frontend: Pokedex 18-type filter buttons (emoji + name), PokemonCard type
    emojis replace rarity badge, UserContext Pokemon interface drops rarity.
  - Atlas: `$unset rarity` on 1025 catalog docs (done, verified).
  - Validate: pytest 56 passed, compileall + ruff clean, biome/tsc/build ✓.
- **[4.1–4.4]** Phase 4 complete — Pokémon frontend live:
  - `components/pokemon/PokemonCard.tsx`: shared card (artwork, dex# name,
    level, rarity badge, active star, fallback #dex).
  - `pages/MyPokemon.tsx`: active partner card + owned grid with Set Active
    (POST `/pokemon/set_active`), empty state pointing to `/starter`.
  - `pages/Pokedex.tsx`: paged catalog browse (60/page, rarity filter,
    load-more) via GET `/shop/pokemon`.
  - `App.tsx`: tabs `mypokemon`/`pokedex` + aliases (pokemon, my_pokemon, dex);
    `NavigationDrawer`: Pokémon + Pokédex nav items (PawPrint icon).
  - `UserContext`: `Pokemon` interface; `User.pokemon[]` + `current_pokemon`.
  - Backend: POST `/pokemon/set_active` route added (progression.py).
  - Browser-verified via preview 4173 with stubbed telegram + API: both pages
    render, rarity filter + load-more work, set-active toast fires.
  - Validate: biome lint (5 pre-existing warnings), tsc clean, vite build ✓.
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
