# Deploying Seal-Bot to Koyeb

Koyeb runs the backend as a Docker service from `koyeb.yaml` (or via CLI/dashboard).
The frontend is served by the backend out of `backend/static` — no separate host
needed unless you want one.

Koyeb is a good pair for this repo: it deploys from any Git host or a local Docker
image, has a free tier, and its regional edge keeps Telegram webhook traffic close.

## Requirements

- A [Koyeb](https://www.koyeb.com) account (verify email to unlock deploys)
- MongoDB + Redis connection strings and the env values from
  [Env variables](README.md#env-variables-all-platforms)
- Optional: [Koyeb CLI](https://www.koyeb.com/docs/cli/installation) (`koyeb version`)

## Option A — Dashboard

1. **Koyeb Console → Create App**.
2. Name it (e.g. `seal-bot`).
3. **Deployment source**: choose **Git repository** and pick your repo + branch at
   `main`. `koyeb.yaml` at the repo root configures the service automatically:
   one web service, build type Docker, Dockerfile path `backend/Dockerfile`.
4. **Port to bind**: `8080` (the Dockerfile exposes it). Koyeb maps it to HTTP.
5. Add the env variables from [Env variables](README.md#env-variables-all-platforms)
   in the **Environment Variables** section. `WEB_APP_URL` = the HTTPS URL Koyeb
   gives you (e.g. `https://fatuous-bird-<id>.koyeb.app`).
6. **Deploy**. Koyeb builds the image and starts `uvicorn ... --port 8080`.

Health checks are configured in `koyeb.yaml` (`/healthz`). You can also set them in
**App Settings → health check**.

## Option B — CLI

```bash
koyeb login

koyeb app init seal-bot
koyeb service init web \
  --docker-file backend/Dockerfile \
  --ports 8080:http \
  --routes /:8080 \
  --health-check-path /healthz \
  --health-check-interval 30 \
  --regions fra

koyeb service update web \
  --env TOKEN=REDACTED \
  --env SUB_TOKEN=REDACTED \
  --env API_ID=1234567 \
  --env API_HASH=REDACTED \
  --env MONGO_URL=REDACTED \
  --env REDIS_URL=REDACTED \
  --env OWNER_ID=123456789 \
  --env SUDO_USERS=123456789 \
  --env MAIN_GROUP_ID=-1001234567890 \
  --env GALLERY_CHANNEL_ID=-1001234567891 \
  --env LOG_GROUP_ID=-1001234567892 \
  --env WEB_APP_URL=https://<your-service>.koyeb.app \
  --env API_VERSION_PREFIX=v1_7b82

koyeb service redeploy web
koyeb service logs web
```

> The `--env` CLI flag is the documented way to set secrets; Koyeb stores env values
> as secrets at runtime. After the first deploy, prefer the **dashboard → Service →
> Environment variables** editor for managing them (each entry is stored encrypted).

Dashboard env template for copy-paste (fills the dashboard section; one click copies it):

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
STRING_SESSION=
WEB_APP_URL=
MINI_APP_SHORT_NAME=app
API_VERSION_PREFIX=v1_7b82
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=false
```

To use a local image instead of Git: build with `docker build -t seal-bot backend`,
push to a registry, and in the dashboard choose **Docker image** as the source with
`registry.hub.docker.com/<user>/seal-bot:latest`.

## Health and readiness

- `/healthz` returns `200 {"status":"ok"}`.
- `/readyz` reports mongo/redis/bot startup state and may return 503 during bot
  startup — fine for Koyeb as long as the container eventually becomes healthy.

## Mini App URL

Set the same value as `WEB_APP_URL` in BotFather (Settings → Mini App URL).

## Region, scale, and restarts

- Pick a region close to your Telegram traffic (e.g. `fra` for Europe).
- **Keep replicas at 1.** Multiple replicas each run their own Telegram client;
  they can duplicate updates and cause conflicts.
- Koyeb **auto-restarts** failed services, and every deployment enjoys an HTTPS
  URL out of the box (`*.koyeb.app`); you can attach a custom domain under
  **Domain** in the app settings.

## Free tier notes

- Koyeb free tier has limited monthly hours; watch the billing dashboard.
- Free services are **not** auto-slept like Heroku free, but deployments with no
  traffic may be suspended to conserve monthly hours — an uptime ping to `/healthz`
  keeps usage visible.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Deploy stuck on *building* | Verify email on the account; then redeploy. |
| Image build fails | Build context defaults to repo root; our Dockerfile needs context `backend/` — `koyeb.yaml` sets `dockerfilePath`, and Koyeb uses that file's directory as context; keep the layout unchanged. |
| Service unhealthy on startup | `/readyz` returns 503 while bots start; raise `health-check-timeout` / interval, or make the first request after logs show "startup complete". |
| 404 on `/api/...` | `API_VERSION_PREFIX` must equal frontend `VITE_API_PREFIX`. |
| Restart loop | Check logs: bad `TOKEN`/`API_HASH`, unreachable `MONGO_URL`/`REDIS_URL`, duplicate clients from replicas >1. |

## References

- [Koyeb Docker deployment](https://www.koyeb.com/docs/run/docker)
- [Koyeb env vars and secrets](https://www.koyeb.com/docs/run/environment-variables)
- [Koyeb health checks](https://www.koyeb.com/docs/run/services/health-checks)
- [Koyeb domains](https://www.koyeb.com/docs/run/domains)
- [Koyeb CLI reference](https://www.koyeb.com/docs/cli/reference)