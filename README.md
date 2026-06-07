# Seal-Bot

Production Telegram character-collection bot, secondary game bot, and Telegram Mini App backend.

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Bun](https://img.shields.io/badge/Bun-1.3-black?logo=bun&logoColor=white)](https://bun.sh/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Compatible-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

Seal-Bot runs a full Telegram bot ecosystem from one Python service:

- A main Telegram bot for character drops, catching, economy, collection, pets, battle pass, staff tools, and Mini App access.
- A secondary game bot for name guessing, quizzes, scramble games, and game leaderboards.
- A FastAPI backend that authenticates Telegram Mini App sessions and serves API, WebSocket, and built React assets.
- A React/Vite/Bun Mini App for profile, gallery, harem, shop, hatchery, battle pass, quests, achievements, staff, and upload workflows.

## Contents

- [Security First](#security-first)
- [Repository Map](#repository-map)
- [Runtime Architecture](#runtime-architecture)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Local Development](#local-development)
- [Validation](#validation)
- [Bot Documentation](#bot-documentation)
- [Mini App Documentation](#mini-app-documentation)
- [API Documentation](#api-documentation)
- [Data Storage](#data-storage)
- [Deployment](#deployment)
- [GitHub Actions](#github-actions)
- [Operations](#operations)
- [Troubleshooting](#troubleshooting)

## Security First

Never commit real bot tokens, Telegram API credentials, MongoDB URLs, Redis URLs, image host keys, or userbot session strings.

`sample.env` is the safe template. Production deployments must provide values through the hosting platform secret manager or a private `.env` file. If any credential-like fallback value in `config.py` has ever been public, rotate it before production use.

Minimum production checklist:

- Rotate every exposed `TOKEN`, `SUB_TOKEN`, `API_HASH`, `MONGO_URL`, `REDIS_URL`, `IMGBB_API_KEY`, and `STRING_SESSION`.
- Keep `.env` out of version control.
- Use HTTPS for `WEB_APP_URL`.
- Configure only trusted Telegram IDs in `OWNER_ID` and `SUDO_USERS`.
- Run only one ASGI worker per bot token. Multiple workers can start duplicate Telegram clients.
- Keep `LOG_FILE_ENABLED=false` in containers unless a writable log volume is configured.

## Repository Map

```text
Seal-bot/
├── Grabber/
│   ├── __init__.py              # Bot clients, global role state, shared exports
│   ├── __main__.py              # Bot-only entrypoint: python -m Grabber
│   ├── client.py                # SealClient, module loading, command sync, safe send helpers
│   ├── runner.py                # Startup/shutdown orchestration
│   ├── core/                    # Cache, sessions, progression, pets, spawns, resources, uploads
│   ├── database/                # MongoDB, Redis, collection exports, indexes
│   ├── modules/                 # Telegram command handlers
│   ├── static/                  # Built Mini App assets served by FastAPI
│   └── webapp/                  # FastAPI app, auth, API routes, WebSocket routes, schemas
├── frontend/
│   ├── src/                     # React Mini App source
│   ├── public/                  # Static frontend assets
│   ├── package.json             # Bun scripts and frontend dependencies
│   ├── bun.lock                 # Frontend lockfile
│   ├── vite.config.js           # Vite config
│   ├── vercel.json              # Vercel static frontend config
│   ├── netlify.toml             # Netlify static frontend config
│   └── wrangler.toml            # Cloudflare Pages config
├── scripts/
│   └── migrate_pets_to_petid.py # Maintenance migration for pet IDs
├── .github/workflows/ci.yml     # Backend, frontend, and Docker CI
├── .python-version              # Python version consumed by local tooling and CI
├── compose.yaml                 # Docker Compose service
├── config.py                    # Environment-driven runtime configuration
├── Dockerfile                   # Multi-stage production image
├── heroku.yml                   # Heroku container deployment
├── pyproject.toml               # Python dependency manifest
├── railway.json                 # Railway Docker deployment config
├── render.yaml                  # Render Blueprint config
├── sample.env                   # Safe environment template
└── uv.lock                      # Python lockfile
```

## Runtime Architecture

### Entrypoints

| Entrypoint | Purpose |
| --- | --- |
| `Grabber.webapp.main:app` | Unified ASGI app. Starts Telegram bots in FastAPI lifespan, serves API and Mini App. |
| `python -m Grabber` | Bot-only process. Starts Telegram bots and idles without FastAPI. |
| `Dockerfile` | Production container. Builds frontend, installs backend dependencies, serves Uvicorn on `$PORT` or `8080`. |

### Bot Clients

`Grabber.__init__` creates three clients:

| Client | Token/session | Purpose |
| --- | --- | --- |
| `app` / `MainBot` | `TOKEN` | Main collection, economy, social, progression, admin, and Mini App bot. |
| `game_bot` / `GameBot` | `SUB_TOKEN` | Secondary game bot for quiz, scramble, and name-guess games. |
| `userbot` / `UserBot` | `STRING_SESSION` | Optional user session used by scraper features. If invalid, scraper features degrade. |

### Startup Flow

`Grabber.runner.start_bots()` performs:

1. Loads sudo role records from MongoDB.
2. Verifies MongoDB connectivity.
3. Verifies Redis connectivity when `REDIS_URL` is configured.
4. Ensures MongoDB indexes.
5. Seeds the pet catalog.
6. Starts main bot, game bot, and optional userbot.
7. Syncs bot command lists with Telegram.
8. Starts deletion, spawn-cache flush, resource monitor, leaderboard sync, and maintenance tasks.
9. Configures the main bot menu button to open `WEB_APP_URL#shop`.

Shutdown cancels background tasks, stops clients, flushes message counts, closes Redis, and closes MongoDB.

### Module Loading

`Grabber.modules.__init__` recursively discovers every Python file under `Grabber/modules`, excluding `__init__.py`. `SealClient._load_modules()` imports each module. Modules either use decorators such as `@app.on_message(...)` or expose `load_handlers(bot)` for explicit handler registration.

## Requirements

Backend:

- Python `>=3.14`
- `uv`
- MongoDB Atlas or compatible MongoDB
- Redis-compatible cache strongly recommended
- Telegram bot token, secondary bot token, API ID, and API hash

Frontend:

- Bun `1.3.14` or compatible with `frontend/package.json`
- React 19, Vite 8, TypeScript, Tailwind CSS v4

Container/deployment:

- Docker for production parity
- Public HTTPS domain for Telegram Mini App use

## Configuration

Create a local environment file from the template:

```bash
cp sample.env .env
```

On Windows PowerShell:

```powershell
Copy-Item sample.env .env
```

Production secrets should be set in the hosting platform, not committed files.

### Required Variables

| Variable | Purpose |
| --- | --- |
| `TOKEN` | Main Telegram bot token. |
| `SUB_TOKEN` | Secondary GameBot token. |
| `API_ID` | Telegram API ID from my.telegram.org. |
| `API_HASH` | Telegram API hash from my.telegram.org. |
| `MONGO_URL` | MongoDB connection string. |
| `WEB_APP_URL` | Public HTTPS URL for the Mini App/backend. |
| `OWNER_ID` | Primary owner Telegram user ID. |

### Recommended Variables

| Variable | Purpose |
| --- | --- |
| `REDIS_URL` | Redis cache for sessions, rate limits, leaderboards, spawn state, and hot reads. |
| `SUDO_USERS` | Comma-separated startup moderators. DB roles can add more later. |
| `MAIN_GROUP_ID` | Main community/group ID used for some logs and giveaway notifications. |
| `GALLERY_CHANNEL_ID` | Channel where uploaded character media is posted or edited. |
| `LOG_GROUP_ID` | Review/log group for startup reports, scraping review, and update proposals. |
| `SUPPORT_CHAT` | Support chat username used in buttons and starter claim checks. |
| `UPDATE_CHAT` | Update channel username used in buttons and starter claim checks. |
| `PHOTO_URL` | Comma-separated fallback/start images. |
| `IMGBB_API_KEY` | Optional image host key used by upload fallback paths. |
| `STRING_SESSION` | Optional userbot session string for scraper access. |
| `MINI_APP_SHORT_NAME` | BotFather Mini App short name. Defaults to `app`. |
| `API_VERSION_PREFIX` | API path prefix. Defaults to `v1_7b82`. |

### Logging Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `LOG_FORMAT` | `text` | `text` or `json`. Use `json` for centralized logging. |
| `LOG_DIR` | `logs` | Directory for rotating file logs. |
| `LOG_FILE` | `seal-bot.log` | Log filename. |
| `LOG_FILE_ENABLED` | `false` | Write rotating file logs in addition to stdout. |
| `LOG_MAX_BYTES` | `10485760` | Max bytes per log file. |
| `LOG_BACKUP_COUNT` | `5` | Rotated log retention count. |
| `LOG_UTC` | `true` | Use UTC timestamps. |

### Resource Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `RESOURCE_MONITOR_ENABLED` | `true` | Enable process memory/task monitoring. |
| `RESOURCE_CHECK_INTERVAL_SECONDS` | `60` | Monitor interval. |
| `RESOURCE_MEMORY_SOFT_LIMIT_MB` | `0` | Soft RSS limit. `0` auto-detects. |
| `RESOURCE_MEMORY_HARD_LIMIT_MB` | `0` | Hard RSS limit. `0` auto-detects. |
| `RESOURCE_MIN_AVAILABLE_MB` | `0` | Minimum host available memory threshold. |
| `RESOURCE_GC_COOLDOWN_SECONDS` | `120` | Minimum delay between cleanup attempts. |
| `RESOURCE_TASK_SOFT_LIMIT` | `500` | Background task warning threshold. |
| `RESOURCE_SHUTDOWN_TIMEOUT_SECONDS` | `10` | Graceful task shutdown timeout. |
| `RESOURCE_REDIS_PURGE_BATCH_SIZE` | `100` | Volatile Redis keys purged per cleanup pass. |
| `REDIS_MEMORY_LIMIT_MB` | `0` | Redis memory budget override. |

## Local Development

Install backend dependencies:

```bash
uv sync
```

Install frontend dependencies:

```bash
cd frontend
bun install
```

Run the unified backend and bot service:

```bash
uv run uvicorn Grabber.webapp.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Run only the Telegram bots:

```bash
uv run python -m Grabber
```

Run the frontend dev server:

```bash
cd frontend
bun run dev
```

Build the frontend:

```bash
cd frontend
bun run build
```

The production Docker build copies `frontend/dist` into `Grabber/static`. For local static serving through FastAPI without Docker, build the frontend and copy the generated `dist` files into `Grabber/static`.

## Validation

Backend syntax/import validation:

```bash
uv run python -m compileall -q config.py Grabber scripts
```

Frontend validation:

```bash
cd frontend
bun run lint
bun run type-check
bun run build
```

Production image validation:

```bash
docker build -t seal-bot:ci .
```

There is no committed pytest/unittest suite in this repository at the moment. CI validates backend compilation, frontend lint/type/build, and Docker build parity.

## Bot Documentation

### Core Game Loop

1. In group chats, non-bot messages are tracked by global sync handlers.
2. Spawn frequency depends on recent active users:
   - `6+` active users: base spawn every `40` messages.
   - `3-5` active users: base spawn every `60` messages.
   - Lower activity: chat frequency or up to `80` messages.
3. Golden Hour runs from `20:00` through `22:59` UTC and halves the target message count.
4. A character spawn stores active state in Redis with MongoDB fallback.
5. Users catch with `/seal <name>`.
6. Correct catches atomically clear the active spawn, add the character, increment chat totals, grant XP, update quests, and check achievements.

`/seal` matching accepts exact normalized names and non-trivial word subsets. Example: `Light` can catch `Light Yagami`, but one-letter guesses are rejected.

### Currencies

| Currency | Symbol | Use |
| --- | --- | --- |
| Shards | `⬪` | Main currency from catches, daily/weekly rewards, games, hunting, and transfers. |
| Zenith | `⧫` | Premium shop currency for character and pet purchases. |
| Telegram Stars | `XTR` | Battle pass premium/elite purchases. |

Important constants:

- `10,000` Shards = `1` Zenith.
- Buying one level costs `10,000` Shards.
- Battle pass Stars prices: Premium `24`, Elite `49`.

### Roles And Permissions

| Role | Source | Can upload | Can edit/admin | Benefits |
| --- | --- | --- | --- | --- |
| Owner | `OWNER_ID` | Yes | Yes | Highest staff perks and all owner commands. |
| Moderator | `SUDO_USERS` or DB role | Yes | Yes | Upload reward, daily/weekly bonuses, shop discount, sell bonus. |
| Uploader | DB role | Yes | No character edit/admin | Upload reward and smaller economy perks. |

Owner can manage DB-backed staff roles with `/addsudo`, `/rmsudo`, and `/sudolist`.

### Main Bot Commands

Core and profile commands:

| Command | Scope | Description |
| --- | --- | --- |
| `/start [payload]` | Private/group | Register or open dashboard. Supports referral, locate, and claim deep-link payloads. |
| `/help` | Any | Interactive help menu. |
| `/webapp` | Any | Sends Mini App button. |
| `/profile`, `/myprofile`, `/me`, `/status`, `/mystatus` | Any | Collector profile, rank, XP, wallet, favorite, active pet, achievements, and collection stats. |
| `/ping` | Any | Bot latency, DB latency, uptime, memory, CPU, and Python/runtime details. |
| `/stats` | Any | Bot totals for characters, users, groups, DB latency, and uptime. |
| `/check` | Any | Check a character/status target depending on command context. |

Collection commands:

| Command | Scope | Description |
| --- | --- | --- |
| `/claim` | Any | One-time starter character and Shards flow gated by support/update membership checks. |
| `/seal <name>` | Group | Catch the active spawned character. |
| `/harem`, `/collection` | Any | View owned character collection with pagination. |
| `/hmode` | Any | Choose harem display mode, including rarity filtering. |
| `/fav [character_id]`, `/sfav [character_id]` | Any | Set favorite character by ID or by replying to a character message. |
| `/search` | Any | Opens Telegram inline search for characters. |
| `/sips <query>` | Any | Search character database by name, ID, anime, or mixed query. |
| `/sani <anime>` | Any | Search characters by anime title. |
| `/animes` | Any | List anime titles in the database. |
| `/rarities`, `/rarity`, `/rlist` | Any | Character counts by rarity. |
| `/messagecount` | Group | Show total messages, active users, spawn frequency, and messages until next spawn. |

Economy and shop commands:

| Command | Scope | Description |
| --- | --- | --- |
| `/balance`, `/bal` | Any | Show Shards and Zenith wallet. |
| `/daily` | Group | Claim daily reward and streak reward. |
| `/weekly` | Group | Claim weekly reward. |
| `/bonus` | Any | Bonus/reward status. |
| `/pay <amount>` | Reply | Send Shards to the replied user with confirmation. |
| `/givebalance <amount>` | Reply | User-to-user Shards transfer; staff can grant without paying. |
| `/takebalance <amount>` | Reply/staff | Staff-only Shards deduction from replied user. |
| `/bet <amount> <choice>` | Any | Gamble Shards. |
| `/mtop` | Any | Richest users leaderboard. |
| `/shop` | Any | Open shop hub. |
| `/cshop` | Any | Character shop listing. |
| `/buylevel [amount]` | Any | Buy battle pass levels with Shards. |
| `/exchange [amount]` | Any | Currency exchange help or Shards-to-Zenith conversion. |
| `/zenith <shards>` | Any | Convert Shards to Zenith. |
| `/shard <zenith>` | Any | Convert Zenith to Shards. |
| `/sell <character_id>` | Any | Sell an owned character for Shards with confirmation. |
| `/gift <character_id>` | Reply | Gift an owned character to another user. |
| `/transfer` | Reply | Two-step transfer of the full collection to another user. This clears sender collection after confirmation. |

Social and battle commands:

| Command | Scope | Description |
| --- | --- | --- |
| `/trade <your_char_id> <their_char_id>` | Group | Request a character trade. |
| `/propose` | Reply | Propose to another user. |
| `/referrals` | Any | Referral link and referral stats. |
| `/battle <bet_amount>` | Group/reply | Challenge the replied user to a PvP pet battle. |

Progression, pets, and eggs:

| Command | Scope | Description |
| --- | --- | --- |
| `/quests` | Any | View daily, weekly, and pass missions; claim completed rewards. |
| `/pass` | Any | View battle pass progress, tiers, reward tracks, and purchase buttons. |
| `/level` | Any | Show current level and XP progress. |
| `/paysupport` | Any | Payment support instructions with user ID. |
| `/terms` | Any | Digital purchase terms. |
| `/achievements` | Any | View achievement milestones. |
| `/petshop` | Any | Browse pet catalog. |
| `/buypet <petid>` | Any | Buy a pet by ID. |
| `/mypet`, `/pet`, `/pets` | Any | Manage owned pets and active pet. |
| `/feed` | Any | Feed active pet. |
| `/train` | Any | Train active pet. |
| `/hunt` | Any | Send active pet hunting for rewards and egg chances. |
| `/eggs`, `/hatch` | Any | View eggs, start incubation, and hatch ready eggs. |

Giveaway and redemption:

| Command | Scope | Description |
| --- | --- | --- |
| `/reedem <code>`, `/redeem <code>`, `/claimwaifu <code>` | Any | Redeem a generated character code. |

### Main Bot Admin Commands

| Command | Role | Description |
| --- | --- | --- |
| `/addsudo <user_id> [moderator|uploader]`, `/setsudo`, `/setrole` | Owner | Add or change staff role. Can also be used as a reply. |
| `/rmsudo <user_id>` | Owner | Remove DB-backed staff role. |
| `/sudolist` | Staff | Paginated staff list with role details. |
| `/upload "Name" "Anime" RarityNum` | Uploader+ | Upload character by replying to media. |
| `/upload URL "Name" "Anime" RarityNum` | Uploader+ | Upload character from URL. |
| `/uploadpet ...` | Uploader+ | Upload pet media and stats. Supports reply or URL. |
| `/update <id> field="value"` | Moderator+ | Propose character updates for log-group confirmation. Supports `name`, `anime`, `rarity`, `url`/`img_url`. |
| `/delete <id>`, `/del <id>` | Moderator+ | Delete character after confirmation. |
| `/givecoin <amount>` or `/givecoin <user_id> <amount>` | Moderator+ | Add Shards with confirmation. |
| `/takecoin <amount>` or `/takecoin <user_id> <amount>` | Moderator+ | Remove Shards with confirmation. |
| `/gban user_id|@username|reply [reason]` | Moderator+ | Globally ban a user for the configured TTL. |
| `/ungban user_id|@username|reply` | Moderator+ | Remove global user ban. |
| `/gbangroup chat_id|@chat|here [reason]`, `/gchatban` | Moderator+ | Globally ban a group/channel and make bots leave. |
| `/ungbangroup chat_id|@chat|here`, `/ungchatban` | Moderator+ | Remove global group ban. |
| `/gbanlist [users|groups]` | Moderator+ | List active global bans. |
| `/gbanstatus user_id|chat_id`, `/gbaninfo` | Moderator+ | Inspect global ban status. |
| `/scrape <group_id_or_username> [limit]` | Moderator+ | Scan chat history for character posts and send review cards to `LOG_GROUP_ID`. |
| `/stop_scrape` | Moderator+ | Stop current scraper task for the chat. |
| `/cnow` | Owner/Moderator | Force a character spawn in the current group. |
| `/broadcast` | Owner | Send global broadcast. |
| `/waifugen <waifu_id> <quantity>` | Owner | Generate a limited redemption code and deep link. |
| `/drop <waifu_id> <quantity>` | Owner | Drop claimable character copies into the current chat. |
| `/give <character_id>` | Owner | Give a character directly. |
| `/mongobackup <source_mongo> <destination_mongo> <db_name>` | Owner | Copy MongoDB database data. |
| `/tgm` | Any configured handler | Telegram media upload helper. |
| `/e`, `/ev`, `/eva`, `/eval`, `/x`, `/ex`, `/exe`, `/exec`, `/py` | Authorized eval users | Execute Python code. Dangerous; keep access narrow. |
| `/clearlocals` | Authorized eval users | Clear eval locals. |

Character upload rarity numbers are defined in `Grabber/modules/collection/rarities.py`. Pet upload format:

```text
/uploadpet "Name" "Rarity" HP ATK SPD Luck Price ReqLevel "Ability" "Description" [petid] [sort_order] [enabled]
```

### GameBot Commands

The secondary bot uses `SUB_TOKEN` and has a separate command list:

| Command | Scope | Description |
| --- | --- | --- |
| `/start`, `/help` | Any | GameBot help and command overview. |
| `/nguess` | Group | Start a character image/name guessing round. |
| `/quiz` | Any | Anime trivia quiz using OpenTDB category 31 with fallback cache. |
| `/scramble` | Group | Unscramble a character name for Shards. |
| `/top` | Any | GameBot rankings. |
| `/stats` | Any | Name guess, quiz, scramble, reward, and top player totals. |

### Rarities, Eggs, And Pass

Rarities are configured in `Grabber/modules/collection/rarities.py`; shop prices, stock limits, payouts, egg tiers, and leaderboard metrics are in `Grabber/core/constants.py`.

Egg tiers:

| Tier | Typical pool | Incubation |
| --- | --- | --- |
| Common | Common/Medium | 4 minutes |
| Golden | Rare/Legendary | 20 minutes |
| Void | Cosmic/Immortal/Exclusive | 75 minutes |
| Rare | Rare through Immortal | 120 minutes |
| Legendary | Exclusive/Eternal/Royal/Mythical | 240 minutes |
| Celestial | Celestial/Divine/Astral/Prestige | 420 minutes |

Battle pass season is configured in `Grabber/core/pass_config.py`:

- Current season: `s1`, `Ascendant Tide`.
- Max level: `100`.
- Tiers: `free`, `premium`, `elite`.
- Premium and elite alter rewards, hunt multipliers, XP multipliers, incubation speed, egg quality, bonus egg chance, and incubation slots.

## Mini App Documentation

The Mini App is a React single-page app under `frontend/`. It authenticates with Telegram `initData`, stores a bearer session, and calls the FastAPI API under `/api/{API_VERSION_PREFIX}`.

Screens/tabs:

| Tab | Route aliases |
| --- | --- |
| Profile | `profile`, `home`, `me`, `harem`, `collection`, `inventory` |
| Hatchery | `incubation`, `eggs`, `hatch`, `hatching`, `incubator` |
| Shop | `shop`, `market`, `cshop`, `store`, `daily_shop`, `dailyshop` |
| Exchange | `exchange`, `currency`, `conversion`, `zenith`, `shard`, `shards` |
| Gallery | `gallery`, `catalog`, `characters` |
| Pet Shop | `pets`, `petshop`, `pet_store`, `companionshop` |
| My Pets | `mypets`, `mypet`, `pet`, `companions` |
| Upload | `upload`, `uploads`, `admin` |
| Staff | `staff`, `sudo`, `sudos`, `contributors`, `contributions` |
| Referrals | `referrals`, `referral`, `invite` |
| Quests | `quests`, `quest`, `tasks`, `missions` |
| Pass | `pass`, `battlepass`, `battle_pass`, `bp` |
| Leaderboard | `leaderboard`, `leaderboards`, `top`, `ranks` |
| Achievements | `achievements`, `achievement`, `badges` |

Open a tab directly with hashes such as:

```text
https://your-backend.example.com#shop
https://your-backend.example.com#gallery
https://your-backend.example.com#pass
```

If the frontend is hosted separately from the backend, set:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Backend origin, for example `https://api.example.com`. |
| `VITE_API_PREFIX` | Same value as backend `API_VERSION_PREFIX`. |

## API Documentation

FastAPI disables public OpenAPI/Swagger routes in runtime config. Route prefix:

```text
/api/{API_VERSION_PREFIX}
```

Default:

```text
/api/v1_7b82
```

Health routes outside the prefix:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz` | Lightweight process health. |
| `GET` | `/readyz` | MongoDB, Redis, and resource readiness. |

API route groups:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/secure_init` | Validate Telegram Mini App `initData` and issue session token. |
| `GET` | `/bot/info` | Bot and Mini App public metadata. |
| `GET` | `/achievements/list` | Achievement definitions. |
| `GET` | `/me` | Current authenticated user profile. |
| `GET` | `/profile` | Compatibility profile endpoint. |
| `GET` | `/leaderboard` | Leaderboard data. |
| `GET` | `/stats` | User/stat summary. |
| `GET` | `/rarities` | Rarity list/count metadata. |
| `GET` | `/character/{char_id}` | Character detail. |
| `GET` | `/harem` | Paginated user harem. |
| `POST` | `/recycle/preview` | Preview recycle result. |
| `POST` | `/character/sell/{char_id}` | Sell owned character. |
| `POST` | `/recycle` | Recycle selected characters. |
| `GET` | `/gallery` | Paginated public gallery. |
| `GET` | `/quests` | Current quests. |
| `POST` | `/quests/claim/{quest_id}` | Claim completed quest. |
| `POST` | `/pets/set_active/{pet_ref}` | Set active pet. |
| `POST` | `/eggs/incubate/{egg_id}` | Start egg incubation. |
| `POST` | `/eggs/hatch/{egg_id}` | Hatch ready egg. |
| `GET` | `/shop/hub` | Shop hub payload. |
| `GET` | `/shop/exchange` | Exchange metadata. |
| `POST` | `/shop/exchange/{direction}` | Convert Shards/Zenith. |
| `GET` | `/shop/characters` | Character shop inventory. |
| `POST` | `/shop/buy/character/{char_id}` | Buy shop character. |
| `GET` | `/shop/pets` | Pet shop inventory. |
| `POST` | `/shop/buy/pet/{pet_ref}` | Buy pet. |
| `GET` | `/shop/battlepass` | Battle pass shop data. |
| `POST` | `/shop/upgrade_pass/{tier}` | Upgrade pass entitlement. |
| `POST` | `/shop/pass_invoice/{tier}` | Create Telegram Stars invoice. |
| `GET` | `/pass_data` | Current pass state. |
| `POST` | `/claim_bank` | Claim pass bank after upgrade. |
| `POST` | `/claim_level/{level}` | Claim level reward. |
| `POST` | `/buy_level` | Buy levels with Shards. |
| `GET` | `/trade/offers` | Trade offers. |
| `POST` | `/trade/offer` | Create trade offer. |
| `POST` | `/trade/respond/{trade_id}` | Accept/decline trade. |
| `GET` | `/social/marriage` | Marriage/proposal state. |
| `GET` | `/social/referrals` | Referral list. |
| `GET` | `/social/referrals/stats` | Referral stats. |
| `GET` | `/battle/stats` | Battle stats. |
| `GET` | `/admin/sudos/contributions` | Staff contribution data. |
| `GET` | `/admin/upload/options` | Upload form options. |
| `PATCH` | `/admin/character/{char_id}` | Staff character update. |
| `POST` | `/admin/upload/character` | Staff character upload. |
| `POST` | `/admin/upload/pet` | Staff pet upload. |
| `WS` | `/ws/leaderboard` | Leaderboard WebSocket updates. |

Authentication:

- `/secure_init` validates Telegram `initData` against `TOKEN` and `SUB_TOKEN`.
- `auth_date` must be within 24 hours with 5 minutes clock skew.
- Sessions last 1 hour.
- Bearer tokens are looked up in Redis with MongoDB fallback.
- Authenticated routes are rate-limited to 30 requests per user per 60 seconds.
- Staff/upload routes require role checks.

Security headers:

- `X-Request-ID`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy`
- CSP allowing self, Telegram scripts/frames, HTTPS images/media, and websocket connections.

## Data Storage

MongoDB database name: `Character_catchers`.

Important collections:

| Export | Mongo collection | Purpose |
| --- | --- | --- |
| `collection` | `anime_characterss` | Character catalog. |
| `user_collection` | `user_collectionsss` | Users, wallets, harem, pets, eggs, progression. |
| `group_collection` | `total_groups` | Registered groups. |
| `user_totals_collection` | `user_totalssss` | Legacy/user totals. |
| `message_counts_collection` | `message` | Group message counters and per-user activity. |
| `group_user_totals_collection` | `group_user_totals` | Per-group catch totals. |
| `sudo_collection` | `sudos` | DB-backed staff roles. |
| `spawns_collection` | `active_spawns` | Active spawn state fallback. |
| `sessions_collection` | `active_sessions` | Auth, giveaway, trade, update, and temporary sessions. |
| `quiz_questions_collection` | `quiz_questions` | Quiz fallback/cache data. |
| `gamebot_enabled_groups_collection` | `nguess_enabled_groups` | GameBot group state. |
| `deletion_queue_collection` | `deletion_queue` | Scheduled message deletions. |
| `daily_shop_collection` | `daily_shop_inventory` | Shop inventory state. |
| `scraped_characters_collection` | `scraped_characters` | Scraper dedupe/review history. |
| `star_orders_collection` | `star_orders` | Telegram Stars pass orders. |
| `global_user_bans_collection` | `global_user_bans` | Global user bans. |
| `global_group_bans_collection` | `global_group_bans` | Global group/channel bans. |
| `pet_catalog_collection` | `pet_catalog` | Pet catalog and uploaded pets. |

Indexes are created during startup by `seal_db.ensure_indexes()`.

Redis is used for:

- Auth sessions and bearer token lookup.
- Rate limiting.
- Spawn state and active users.
- Message count hot path.
- Leaderboard sorted sets.
- Search/update temporary data.
- Cache invalidation and high-frequency reads.

Most paths have MongoDB or bounded in-process fallbacks, but production should run Redis for reliability and performance.

## Deployment

### Docker

Build and run:

```bash
docker build -t seal-bot .
docker run --env-file .env -p 8080:8080 seal-bot
```

Compose:

```bash
docker compose up -d --build
docker compose logs -f seal-bot
```

The image:

- Builds the frontend with `oven/bun`.
- Installs Python dependencies with `uv`.
- Runs on Python 3.14 slim.
- Runs as non-root `botuser`.
- Serves Uvicorn on `${PORT:-8080}`.
- Health-checks `/healthz`.

### Heroku

This repo includes `heroku.yml` and `Procfile`.

```bash
heroku login
heroku create your-app-name --stack container
heroku stack:set container
heroku config:set TOKEN=REDACTED
heroku config:set MONGO_URL=REDACTED
heroku config:set OWNER_ID=... SUDO_USERS=...
git push heroku main
heroku logs --tail
```

### Render

`render.yaml` defines a Docker web service named `seal-bot`, `/healthz` health check, and secret placeholders. Fill every `sync: false` variable in the Render dashboard before deploy.

### Railway

`railway.json` uses the root Dockerfile, `/healthz`, and restart-on-failure policy. Add required variables in Railway Variables and deploy.

### VPS

Recommended:

- Docker and Docker Compose plugin.
- Caddy or Nginx for HTTPS.
- Managed MongoDB and Redis.
- One running container per bot token.

```bash
git clone <repo-url> /opt/seal-bot
cd /opt/seal-bot
cp sample.env .env
docker compose up -d --build
docker compose logs -f seal-bot
```

Proxy HTTPS traffic to `http://127.0.0.1:8080`.

### Static Frontend Providers

Use Vercel, Netlify, Cloudflare Pages, or Wasmer Edge for frontend-only hosting. The Python backend must still run on a persistent host because it starts Telegram clients, background workers, MongoDB clients, and Redis clients.

Before deploying the frontend separately:

1. Deploy the backend first on Docker, Render, Railway, Heroku, VPS, or another persistent Python host.
2. Choose the final frontend URL, for example `https://seal-mini-app.vercel.app`.
3. Set backend `WEB_APP_URL` to that frontend URL. The backend uses `WEB_APP_URL` for CORS and for the Telegram menu button.
4. Set backend `API_VERSION_PREFIX` and keep the frontend `VITE_API_PREFIX` identical.
5. In BotFather, set the Mini App URL to the frontend URL.
6. Rebuild the frontend any time `VITE_API_URL` or `VITE_API_PREFIX` changes. Vite bakes `VITE_*` values into the static build.

Required frontend build variables:

| Variable | Example | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `https://seal-backend.example.com` | Public backend origin. Do not include `/api/...`. |
| `VITE_API_PREFIX` | `v1_7b82` | Must match backend `API_VERSION_PREFIX`. |

Common static build settings:

| Provider | Root/base | Install command | Build command | Output |
| --- | --- | --- | --- | --- |
| Vercel | `frontend` | `bun install --frozen-lockfile` | `bun run build` | `dist` |
| Netlify | `frontend` | Auto-detected from `bun.lock`, or `bun install --frozen-lockfile` | `bun run build` | `dist` |
| Cloudflare Pages | `frontend` | Auto install, or `bun install --frozen-lockfile` | `bun run build` | `dist` |
| Wasmer Edge | `frontend` | Local install before deploy | `bun run build` | `dist` |

The repo already includes:

- `frontend/vercel.json` with `bun run build`, `dist`, and SPA rewrite.
- `frontend/netlify.toml` with `bun run build`, `dist`, and SPA rewrite.
- `frontend/public/_redirects`, copied into `dist`, for SPA fallback on Netlify/Cloudflare-style static routing.
- `frontend/wrangler.toml` with `pages_build_output_dir = "dist"` for Cloudflare Pages.

#### Vercel

Dashboard deployment:

1. Open Vercel and import the Git repository.
2. Set Root Directory to `frontend`.
3. Use framework preset `Vite`.
4. Confirm build settings:
   - Install Command: `bun install --frozen-lockfile`
   - Build Command: `bun run build`
   - Output Directory: `dist`
5. Add environment variables for Production, Preview, and Development:
   - `VITE_API_URL=https://your-backend.example.com`
   - `VITE_API_PREFIX=v1_7b82`
6. Deploy.
7. Copy the production Vercel URL into backend `WEB_APP_URL`.
8. Redeploy or restart the backend so CORS and the bot menu button use the frontend URL.
9. Configure the same frontend URL in BotFather.

CLI deployment:

```bash
cd frontend
bun install --frozen-lockfile
vercel
vercel --prod
```

`frontend/vercel.json` is intentionally committed, so Vercel has the correct build command, output directory, and SPA rewrite even if dashboard auto-detection changes.

#### Netlify

Dashboard deployment:

1. Open Netlify and create a new project from Git.
2. Select this repository.
3. Set Base directory to `frontend`.
4. Confirm build settings:
   - Build command: `bun run build`
   - Publish directory: `dist`
5. Add environment variables:
   - `VITE_API_URL=https://your-backend.example.com`
   - `VITE_API_PREFIX=v1_7b82`
   - Optional: `BUN_VERSION=1.3.14` if you want to pin the Netlify build image's Bun version.
6. Deploy.
7. Set backend `WEB_APP_URL` to the Netlify site URL or custom domain.
8. Update BotFather with the same frontend URL.

Manual CLI deployment:

```bash
cd frontend
bun install --frozen-lockfile
bun run build
netlify login
netlify init
netlify deploy --dir=dist
netlify deploy --prod --dir=dist
```

`frontend/netlify.toml` and `frontend/public/_redirects` keep direct frontend routes from returning 404. Keep both files when deploying this Mini App as a single-page app.

#### Cloudflare Pages

Dashboard deployment:

1. Open Cloudflare Dashboard.
2. Go to Workers & Pages.
3. Create a Pages project and connect the Git repository.
4. Set Project root directory to `frontend`. Do not set this to `dist`; Cloudflare checks the root directory immediately after cloning, before the build creates `dist`.
5. Use framework preset `React (Vite)` or configure manually:
   - Build command: `bun run build`
   - Build output directory: `dist`
   - Deploy command: leave empty. Do not set this to `bun run deploy` for normal Cloudflare Pages Git deployments.
6. Add environment variables:
   - `VITE_API_URL=https://your-backend.example.com`
   - `VITE_API_PREFIX=v1_7b82`
7. Deploy.
8. Set backend `WEB_APP_URL` to the Cloudflare Pages URL or custom domain.
9. Update BotFather with that frontend URL.

If your Cloudflare log says `It seems that you have run wrangler deploy on a Pages project`, remove `npx wrangler deploy` from the project settings. For a Pages project connected to Git, use the dashboard build/output settings above and leave Deploy command empty. `wrangler deploy` is for Workers and expects a Worker entry point or Workers static assets config.

Direct upload with Wrangler:

```bash
cd frontend
bun install --frozen-lockfile
bun run build
bunx wrangler pages deploy dist --project-name seal-bot-frontend
```

You can run the same flow through the committed scripts:

```bash
cd frontend
bun run deploy:cloudflare
```

Only use a deploy command for manual/direct upload workflows outside the normal Cloudflare Pages Git build. In that case, after the app has already been built, use:

```bash
bun run deploy
```

Cloudflare's React/Vite Pages preset uses `dist` as the build output. The committed `frontend/wrangler.toml` also declares `pages_build_output_dir = "dist"`.

#### Wasmer Edge

Wasmer Edge can host the built React/Vite frontend as a static site, but this repo does not commit Wasmer config because `owner`, package name, and app name are account-specific.

Wasmer is only for the static Mini App here. It does not replace the Python backend.

One-time setup:

```bash
wasmer login
cd frontend
wasmer app create --template static-site
```

When prompted, create a new package/app under your Wasmer username or organization. The command generates `wasmer.toml`, `app.yaml`, and usually a `public` directory.

Edit the generated `wasmer.toml` so Wasmer serves the Vite build output:

```toml
[package]
name = "<wasmer-owner>/seal-bot-frontend"
version = "0.1.0"
description = "Seal Bot Telegram Mini App frontend"

[dependencies]
"sharrattj/static-web-server" = "1"

[fs]
public = "dist"
```

If you want direct paths such as `/shop` or `/gallery` to work, add SPA fallback arguments to `app.yaml`:

```yaml
kind: wasmer.io/App.v0
owner: <wasmer-owner>
name: seal-bot-frontend
package: <wasmer-owner>/seal-bot-frontend
cli_args:
  - --page-fallback
  - ./dist/index.html
```

Build and deploy:

```bash
cd frontend
bun install --frozen-lockfile
```

Create or update `frontend/.env.production` before building:

```env
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

Then build, test, and deploy:

```bash
bun run build
wasmer run . -- --port 9000 --page-fallback ./dist/index.html
wasmer deploy
```

After Wasmer returns the app URL, set backend `WEB_APP_URL` to that URL and configure the same URL in BotFather.

Provider references:

- [Vercel Vite deployment](https://vercel.com/docs/frameworks/frontend/vite)
- [Netlify Vite deployment](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/)
- [Cloudflare Pages React deployment](https://developers.cloudflare.com/pages/framework-guides/deploy-a-react-site/)
- [Cloudflare Pages build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)
- [Wasmer React static site guide](https://docs.wasmer.io/edge/guides/react-static-site/)

## GitHub Actions

The CI workflow in `.github/workflows/ci.yml` runs on pushes to `main`, pull requests, and manual dispatch.

Jobs:

| Job | Checks |
| --- | --- |
| Backend | Checkout, Python from `.python-version`, `uv sync --frozen --no-dev`, `compileall` for `config.py`, `Grabber`, and `scripts`. |
| Frontend | Checkout, Bun from `frontend/package.json`, frozen Bun install, ESLint, TypeScript check, Vite build. |
| Docker | Builds the production Dockerfile after backend and frontend checks pass. |

## Operations

Health:

```bash
curl https://your-domain.example.com/healthz
curl https://your-domain.example.com/readyz
```

Readiness returns `503` when MongoDB, Redis, or hard resource pressure makes the service degraded.

Operational notes:

- Use `/ping` for runtime system metrics from Telegram.
- Use `/stats` for bot totals.
- Use `/messagecount` in groups to inspect spawn cadence.
- Use `/gbanlist` and `/gbanstatus` for global ban audit.
- Check `LOG_GROUP_ID` for startup reports, scraper review, and update confirmations.
- Rebuild the frontend and image after changing Mini App source.
- Keep Telegram BotFather Mini App URL aligned with `WEB_APP_URL`.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Bot does not start | Verify `TOKEN`, `SUB_TOKEN`, `API_ID`, `API_HASH`, MongoDB connectivity, and that only one process uses each bot token. |
| Startup says Redis degraded | Verify `REDIS_URL`, TLS scheme, credentials, and provider firewall rules. |
| Mini App returns `401` | Session token is missing, expired, or not in Redis/Mongo fallback. Reopen from Telegram. |
| Mini App returns `403` | Telegram `initData` failed or staff endpoint was accessed without role permission. |
| Mini App cannot authenticate | `WEB_APP_URL` must match the public HTTPS URL configured in BotFather. |
| Static route shows stale UI | Rebuild frontend and Docker image, or refresh `Grabber/static`. |
| Scraper fails | Check `STRING_SESSION`, userbot startup logs, and membership in target chat. |
| Character upload fails | Check media size, URL validity, Catbox/ImgBB availability, `IMGBB_API_KEY`, and uploader role. |
| `/readyz` is degraded | Inspect JSON response for `mongo`, `redis`, and `resources` details. |
| Duplicate updates or repeated bot replies | Confirm the host is running one worker/process per token. |

## License

This project is licensed under the terms in [LICENSE](LICENSE).
