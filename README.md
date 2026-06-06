# Seal-Bot

Production-oriented Telegram bot and Mini App service for character collection, economy, progression, social features, and lightweight game interactions.

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Compatible-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Overview

Seal-Bot runs a Telegram bot ecosystem and a React-based Telegram Mini App from a single ASGI service. FastAPI serves the API and static Mini App assets, while the application lifespan starts and stops the Telegram clients in the same process. This keeps bot state, database clients, cache clients, request handling, and background workers under one runtime lifecycle.

The service is built for container deployment and includes health checks, readiness checks, redacted logging, request correlation IDs, Redis-backed hot paths, MongoDB durability, rate limiting, and resource pressure monitoring.

## Capabilities

- Telegram bot modules for collection, economy, progression, games, social workflows, admin utilities, and informational commands.
- Telegram Mini App screens for profile, gallery, harem, shop, quests, battle pass, pets, referrals, achievements, and leaderboards.
- HMAC validation of Telegram `initData`, expiring bearer sessions, and protected API routes.
- MongoDB-backed durable state with Redis acceleration for sessions, rate limits, cache-heavy reads, and leaderboard data.
- Production container build with a multi-stage Dockerfile, non-root runtime user, and HTTP health check.
- Operational safeguards including structured or text logging, secret redaction, graceful shutdown, background task tracking, and memory pressure cleanup.

## Architecture

```text
Seal-bot/
├── Grabber/
│   ├── core/              # Cache, sessions, resources, tasks, game logic, utilities
│   ├── database/          # MongoDB and Redis connection layer
│   ├── modules/           # Telegram bot feature modules
│   ├── static/            # Built Mini App assets served by FastAPI
│   └── webapp/            # FastAPI app, auth, routes, schemas, websocket routes
├── frontend/              # React, Vite, TypeScript, Tailwind Mini App source
├── scripts/               # Maintenance and migration scripts
├── config.py              # Environment-driven runtime configuration
├── compose.yaml           # VPS/local Docker Compose runtime
├── sample.env             # Example local environment file
├── pyproject.toml         # Python dependency manifest
├── Dockerfile             # Production container image
├── heroku.yml             # Heroku container deployment definition
├── render.yaml            # Render Blueprint deployment definition
├── railway.json           # Railway Docker deployment definition
└── Procfile               # PaaS process definition
```

Runtime entrypoints:

- Web service: `Grabber.webapp.main:app`
- Bot-only runner: `python -m Grabber`
- Health check: `GET /healthz`
- Readiness check: `GET /readyz`
- API prefix: `/api/{API_VERSION_PREFIX}` with `v1_7b82` as the default

> Run one ASGI worker per bot token. Multiple workers can start duplicate Telegram clients and compete for updates.

## Tech Stack

Backend:

- Python `>=3.14`
- FastAPI and Uvicorn
- Kurigram/Pyrogram Telegram clients
- PyMongo `AsyncMongoClient`
- `redis.asyncio`
- Pydantic, ORJSON, HTTPX, psutil

Frontend:

- Node.js `>=22`
- React 19
- Vite 8
- TypeScript
- Tailwind CSS v4
- ESLint, Framer Motion, Lucide React

Infrastructure:

- Docker multi-stage production image
- MongoDB Atlas or compatible MongoDB deployment
- Redis-compatible managed cache
- Heroku, Render, Koyeb, Fly.io, or another container-capable PaaS

## Prerequisites

- Python 3.14+
- `uv` for Python dependency management
- Bun 1.3+ for frontend dependency management and builds
- MongoDB connection string
- Redis connection string recommended for production
- Telegram bot token, Telegram API ID, and Telegram API hash
- Docker for containerized deployment

## Configuration

Create a local environment file from the sample:

```bash
cp sample.env .env
```

Production deployments should configure secrets through the platform secret manager. Do not commit `.env` files, bot tokens, API hashes, database credentials, Redis credentials, or session strings.

Required production variables:

| Variable | Purpose |
| --- | --- |
| `TOKEN` | Primary Telegram bot token. |
| `SUB_TOKEN` | Secondary game bot token. |
| `API_ID` | Telegram API ID. |
| `API_HASH` | Telegram API hash. |
| `MONGO_URL` | MongoDB connection string. |
| `WEB_APP_URL` | Public HTTPS URL used by the Telegram Mini App. |
| `OWNER_ID` | Primary owner or operator Telegram user ID. |

Recommended variables:

| Variable | Purpose |
| --- | --- |
| `REDIS_URL` | Redis-compatible cache URL for sessions, rate limits, and high-frequency reads. |
| `SUDO_USERS` | Comma-separated privileged operator IDs. |
| `MAIN_GROUP_ID` | Primary community or game group ID. |
| `GALLERY_CHANNEL_ID` | Channel used for gallery/media workflows. |
| `LOG_GROUP_ID` | Telegram group used for operational logging workflows. |
| `SUPPORT_CHAT` | Public support chat username or link. |
| `UPDATE_CHAT` | Public updates channel username. |
| `IMGBB_API_KEY` | Image upload integration key. |
| `STRING_SESSION` | Optional userbot session for scraper-related features. |
| `MINI_APP_SHORT_NAME` | BotFather Mini App short name. Defaults to `app`. |
| `API_VERSION_PREFIX` | Obfuscated API route prefix. Defaults to `v1_7b82`. |

Logging variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `LOG_FORMAT` | `text` | Use `text` or `json`. |
| `LOG_FILE_ENABLED` | `false` | Enable rotating file logs in addition to stdout. |
| `LOG_DIR` | `logs` | Directory for rotating file logs. |
| `LOG_FILE` | `seal-bot.log` | Log filename. |
| `LOG_MAX_BYTES` | `10485760` | Maximum bytes per log file. |
| `LOG_BACKUP_COUNT` | `5` | Number of rotated log files to retain. |
| `LOG_UTC` | `true` | Use UTC timestamps. |

Resource management variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `RESOURCE_MONITOR_ENABLED` | `true` | Enable process resource monitoring. |
| `RESOURCE_CHECK_INTERVAL_SECONDS` | `60` | Monitor interval. |
| `RESOURCE_MEMORY_SOFT_LIMIT_MB` | `0` | Soft RSS limit. `0` auto-detects from the host or cgroup. |
| `RESOURCE_MEMORY_HARD_LIMIT_MB` | `0` | Hard RSS limit. `0` auto-detects from the host or cgroup. |
| `RESOURCE_MIN_AVAILABLE_MB` | `0` | Minimum available system memory threshold. |
| `RESOURCE_GC_COOLDOWN_SECONDS` | `120` | Minimum time between cleanup attempts. |
| `RESOURCE_TASK_SOFT_LIMIT` | `500` | Background task warning threshold. |
| `RESOURCE_SHUTDOWN_TIMEOUT_SECONDS` | `10` | Graceful shutdown timeout. |
| `RESOURCE_REDIS_PURGE_BATCH_SIZE` | `100` | Maximum volatile Redis keys purged per cleanup pass. |
| `REDIS_MEMORY_LIMIT_MB` | `0` | Redis memory budget override. `0` uses Redis `maxmemory` when available. |

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

Run the Mini App frontend during active UI development:

```bash
cd frontend
bun run dev
```

Run the unified backend service:

```bash
uv run uvicorn Grabber.webapp.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Run the bot-only process when the web API and Mini App are not needed:

```bash
uv run python -m Grabber
```

Build the frontend:

```bash
cd frontend
bun run build
```

The Docker build copies `frontend/dist` into `Grabber/static` automatically. For local static serving through FastAPI, rebuild the frontend and copy the generated `dist` contents into `Grabber/static`.

## Validation

Frontend checks:

```bash
cd frontend
bun run type-check
bun run lint
bun run build
```

Backend syntax check:

```bash
uv run python -m compileall Grabber config.py
```

UI smoke verification is available through `verify_ui.py`. Start the backend on `http://localhost:8000` first:

```bash
uv run python verify_ui.py
```

## Deployment

### Deployment Compatibility

| Target | Full bot + API backend | Frontend-only Mini App | Notes |
| --- | --- | --- | --- |
| Docker / VPS | Yes | Yes | Best option when you want full control over uptime, logs, and reverse proxying. |
| Heroku | Yes | Served by backend image | Uses `heroku.yml` and the Dockerfile. |
| Render | Yes | Served by backend image | `render.yaml` is included for Blueprint-based setup. |
| Railway | Yes | Served by backend image | `railway.json` is included for Dockerfile deploys and health checks. |
| Vercel | No, not for this backend as-is | Yes | Use for `frontend/` only and point `VITE_API_URL` at the backend. |
| Cloudflare Pages | No, not for this backend as-is | Yes | Use for `frontend/` only and point `VITE_API_URL` at the backend. |
| Netlify | No, not for this backend as-is | Yes | Use for `frontend/` only and point `VITE_API_URL` at the backend. |

The backend needs a persistent Python process because it starts Telegram clients and background workers. Static/serverless platforms are appropriate for the React Mini App only.

### Shared Production Requirements

- Use one ASGI worker per bot token.
- Set `WEB_APP_URL` to the public HTTPS URL that Telegram opens.
- If the frontend is hosted separately, set `VITE_API_URL` to the backend origin and keep `VITE_API_PREFIX` aligned with `API_VERSION_PREFIX`.
- Keep MongoDB and Redis credentials in the host's secret manager.
- Point uptime checks at `/healthz`; use `/readyz` for deeper infrastructure readiness.

### Docker

Build and run the production image locally:

```bash
docker build -t seal-bot .
docker run --env-file .env -p 8080:8080 seal-bot
```

Or use Compose:

```bash
docker compose up -d --build
```

The container:

- builds the frontend with Node 22,
- installs Python dependencies with `uv`,
- runs as a non-root `botuser`,
- serves Uvicorn on `${PORT:-8080}`,
- exposes `/healthz` as the Docker health check.

### Heroku

This repository includes `heroku.yml` for container deployments. Heroku supplies `$PORT`, and the Docker command already binds Uvicorn to that port.

Recommended flow:

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

After deploy, set the Heroku URL in BotFather as the Mini App URL.

### Render

`render.yaml` is included for Blueprint deployments.

1. Create a new Blueprint from this repository.
2. Review the generated web service named `seal-bot`.
3. Fill all `sync: false` environment variables in the Render dashboard.
4. Deploy the service.
5. Set `WEB_APP_URL` to the public Render URL or custom domain.
6. Configure the same URL in BotFather.

Render should use the repository Dockerfile. The included Blueprint sets `/healthz` as the health check path and gives the process extra shutdown time for graceful bot teardown.

### Railway

`railway.json` is included for Dockerfile-based deploys and health checks.

1. Create a Railway project from this repository.
2. Ensure the service uses the root `Dockerfile`.
3. Add the required variables from `sample.env` in Railway Variables.
4. Deploy and confirm `/healthz` returns `{"status":"ok"}`.
5. Set `WEB_APP_URL` to the Railway public domain or custom domain.
6. Configure the same URL in BotFather.

### VPS

Recommended VPS shape:

- Ubuntu LTS or similar Linux distribution.
- Docker and Docker Compose plugin.
- Nginx or Caddy for HTTPS termination.
- MongoDB Atlas or managed MongoDB instead of a database on the same small VPS.
- Managed Redis where possible.

Deployment outline:

```bash
git clone <repo-url> /opt/seal-bot
cd /opt/seal-bot
cp sample.env .env
nano .env
docker compose up -d --build
docker compose logs -f seal-bot
```

Proxy HTTPS traffic to `http://127.0.0.1:8080`, then set `WEB_APP_URL` and the BotFather Mini App URL to the HTTPS domain.

### Vercel Frontend

Use Vercel for the React Mini App only.

Project settings:

- Root directory: `frontend`
- Build command: `bun run build`
- Output directory: `dist`
- Environment variables:
  - `VITE_API_URL=https://your-backend.example.com`
  - `VITE_API_PREFIX=v1_7b82`

`frontend/vercel.json` includes the Vite build output and SPA rewrite settings.

### Netlify Frontend

Use Netlify for the React Mini App only.

Project settings:

- Base directory: `frontend`
- Build command: `bun run build`
- Publish directory: `dist`
- Environment variables:
  - `VITE_API_URL=https://your-backend.example.com`
  - `VITE_API_PREFIX=v1_7b82`

`frontend/netlify.toml` and `frontend/public/_redirects` are included for static build and SPA routing support.

### Cloudflare Pages Frontend

Use Cloudflare Pages for the React Mini App only.

Project settings:

- Root directory: `frontend`
- Framework preset: React / Vite
- Build command: `bun run build`
- Build output directory: `dist`
- Environment variables:
  - `VITE_API_URL=https://your-backend.example.com`
  - `VITE_API_PREFIX=v1_7b82`

`frontend/wrangler.toml` includes the Pages output directory for Wrangler-based workflows.

### Provider References

- [Heroku Container Registry and Runtime](https://devcenter.heroku.com/articles/container-registry-and-runtime)
- [Heroku Docker builds with heroku.yml](https://devcenter.heroku.com/articles/docker-builds-heroku-yml)
- [Render Blueprint YAML reference](https://render.com/docs/blueprint-spec)
- [Railway config as code](https://docs.railway.com/config-as-code/reference)
- [Railway Dockerfiles](https://docs.railway.com/deploy/dockerfiles)
- [Vercel build configuration](https://vercel.com/docs/deployments/configure-a-build)
- [Netlify Vite guide](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/)
- [Cloudflare Pages React guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-react-site/)

## Telegram Mini App Registration

Register the Mini App through [@BotFather](https://t.me/BotFather):

1. Open BotFather and select the primary bot.
2. Go to Bot Settings.
3. Configure the Mini App.
4. Set the public HTTPS `WEB_APP_URL`.
5. Set the short name and mirror it in `MINI_APP_SHORT_NAME` if it differs from `app`.

Telegram `initData` is validated server-side. The Mini App must be opened from Telegram for authenticated API calls.

## API And Security Model

- API routes are mounted under `/api/{API_VERSION_PREFIX}`.
- Public OpenAPI documentation is disabled in production runtime configuration.
- `/secure_init` validates Telegram `initData` with HMAC-SHA256 and issues an expiring session token.
- Authenticated API routes use bearer tokens.
- Redis-backed rate limits protect initialization and authenticated API routes, with bounded in-process fallbacks.
- The service emits security headers including CSP, `X-Content-Type-Options`, referrer policy, and permissions policy.
- CORS is restricted to Telegram Web and the configured `WEB_APP_URL`.
- Logs redact configured secrets and common token/credential patterns before output.

## Operations

Health endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/healthz` | Lightweight process health check. |
| `/readyz` | MongoDB, Redis, and resource pressure readiness check. |

Readiness returns a degraded status when required infrastructure is unavailable or the process crosses hard resource thresholds.

Background work includes leaderboard rebuilds, maintenance tasks, resource monitoring, and bot lifecycle management. Shutdown cancels background tasks, stops bot clients, closes Redis, and closes MongoDB.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Bot fails with API credential errors | Verify `API_ID`, `API_HASH`, `TOKEN`, and `SUB_TOKEN`. |
| Mini App API returns `403` | Open the Mini App inside Telegram and confirm `WEB_APP_URL` matches BotFather. |
| API returns `401` | The bearer token is missing, invalid, or expired. Reinitialize through `/secure_init`. |
| Redis errors appear in logs | Confirm `REDIS_URL`; the service can fall back for some paths, but production should use Redis. |
| Frontend route returns stale UI | Rebuild the frontend and update `Grabber/static`, or rebuild the Docker image. |
| Readiness is degraded | Inspect `/readyz` for MongoDB, Redis, or resource pressure details. |

## Security Checklist

- Override every secret-bearing setting through environment variables in production.
- Rotate any token, API hash, database URL, Redis URL, image host key, or session string that has ever been exposed.
- Keep `.env` files out of version control.
- Use HTTPS for `WEB_APP_URL`.
- Restrict privileged Telegram IDs in `OWNER_ID` and `SUDO_USERS`.
- Keep `LOG_FORMAT=json` for centralized log pipelines and `LOG_FILE_ENABLED=false` for container stdout-only logging unless a writable log volume is configured.
- Deploy only one ASGI worker per bot token.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
