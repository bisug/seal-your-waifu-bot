# Seal-Bot-V2 Deployment Guides

Deploy options for the Seal-Bot stack:

- [Heroku](heroku.md) — backend container, pushes to Git
- [Render](render.md) — backend Docker via Blueprint
- [Koyeb](koyeb.md) — backend Docker via CLI/dashboard
- [Vercel](vercel.md) — frontend Mini App hosting
- [Cloudflare](cloudflare.md) — frontend Mini App hosting (Pages)

## Two parts, two decisions

The repo is a monorepo with two deployable halves:

| Half | What it runs | Needs a persistent host? |
| --- | --- | --- |
| Backend | FastAPI + Telegram bot clients, workers, MongoDB + Redis clients | **Yes** — long-running process. |
| Frontend | React/Vite Telegram Mini App (static build) | No — any static host works. |

### Choose your backend host

| Platform | When to pick it |
| --- | --- |
| Heroku | Want Git-push deploys, no Dockerfile control needed (container stack supported). |
| Render | Free tier with Blueprint-as-code config (`render.yaml`). |
| Koyeb | Regional edge deploys, generous free tier, Docker-first, CLI-driven. |
| VPS / Docker Compose | Full control, persistent volumes, private network. |
| Railway | Docker deploy with health check (`railway.json` already in repo). |

**Not an option:** Vercel and Cloudflare Workers are serverless/short-lived and cannot
run the backend. See [Vercel](vercel.md) and [Cloudflare](cloudflare.md) for why.

### Choose your frontend host

| Platform | When to pick it |
| --- | --- |
| Vercel | Fast builds, Git-integrated, framework-aware. |
| Cloudflare Pages | Edge-cached static files, generous free tier. |

The backend can also serve the built frontend itself (copy `frontend/dist` into
`backend/backend/static` before building the image) — then you do not need a
separate frontend host at all.

---

## Env variables (all platforms)

Required at runtime (create them in the platform's Secrets/Env UI — never commit them):

| Variable | Description |
| --- | --- |
| `TOKEN` | Main bot token from BotFather |
| `SUB_TOKEN` | Secondary game-bot token |
| `API_ID` / `API_HASH` | From my.telegram.org |
| `MONGO_URL` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `OWNER_ID` | Your Telegram user id |
| `SUDO_USERS` | Comma-separated Telegram ids |
| `MAIN_GROUP_ID` / `GALLERY_CHANNEL_ID` / `LOG_GROUP_ID` | Channel/group ids |
| `SUPPORT_CHAT` / `UPDATE_CHAT` | Chat handles |
| `PHOTO_URL` | Public bot photo URL |
| `IMGBB_API_KEY` | imgbb key for uploads |
| `WEB_APP_URL` | Public HTTPS origin of your **frontend** (the Mini App) |
| `MINI_APP_SHORT_NAME` | Short name set in BotFather |
| `API_VERSION_PREFIX` | Must equal frontend `VITE_API_PREFIX` |

Logging (optional, recommended for containers):

| Variable | Recommended |
| --- | --- |
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | `json` |
| `LOG_FILE_ENABLED` | `false` in containers (no writable volume guarantees) |

> **One rule everywhere:** run exactly **one** web worker per bot token.
> Multiple workers start duplicate Telegram clients. Every platform guide
> below enforces `--workers 1`.

### Copy-ready env template

Paste into the platform's env editor, then fill each value (every fenced block has
a copy button on GitHub / VS Code):

```env
TOKEN=
SUB_TOKEN=
API_ID=
API_HASH=
MONGO_URL=
REDIS_URL=
OWNER_ID=
SUDO_USERS=
MAIN_GROUP_ID=
GALLERY_CHANNEL_ID=
LOG_GROUP_ID=
SUPPORT_CHAT=
UPDATE_CHAT=
PHOTO_URL=
IMGBB_API_KEY=
WEB_APP_URL=
MINI_APP_SHORT_NAME=app
API_VERSION_PREFIX=v1_7b82
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=false
```

---

## After the backend is reachable

1. Point `WEB_APP_URL` at the frontend URL you will actually use (or the app's own URL when serving the built frontend).
2. Set the same URL as the Mini App URL in BotFather.
3. If the frontend is hosted separately, rebuild it after changing `VITE_API_URL` / `VITE_API_PREFIX`.
4. Verify `/healthz` and `/readyz`.
5. Watch startup logs for MongoDB, Redis, command sync, and bot menu setup.

See the per-platform guides for exact steps.