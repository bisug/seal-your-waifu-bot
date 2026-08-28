# Deploying Seal-Bot to Render

Render runs the backend from the included `render.yaml` Blueprint as a Docker
service. The frontend is served by the backend out of `backend/backend/static` —
no separate host needed unless you want one (then see the Vercel or Cloudflare guides).

## Requirements

- A [Render](https://render.com) account
- A GitHub/GitLab repo containing this project (Blueprint deploys are Git-connected)
- MongoDB + Redis connection strings and the env values from
  [Env variables](README.md#env-variables-all-platforms)

## 1. Go to `render.yaml`

From the Render dashboard open **New → Blueprint**, select your repo. Render reads
`render.yaml` from the repo root and proposes a single **web service** named
`seal-bot` with `runtime: docker`.

If you prefer not to use the Blueprint, create a normal **Web Service** manually:

```text
Runtime: Docker
Root Directory: .   (repo root — the Blueprint sets dockerContext/dockerfilePath)
Build context: ./backend
Dockerfile path: ./backend/Dockerfile
```

> `render.yaml` already points `dockerContext: ./backend` and
> `dockerfilePath: ./backend/Dockerfile` — the Dockerfile currently uses
> **context-relative** paths (`COPY pyproject.toml uv.lock ./`), so the context must
> stay `./backend`.

## 2. Fill the environment variables

The Blueprint pre-creates the variables listed in `render.yaml`, but **every
variable with `sync: false` must be filled manually on the service** (Render does
not import secrets from the Blueprint). Copy the template from
[Env variables in the guide index](README.md#copy-ready-env-template),
with:

- `WEB_APP_URL` = `https://<your-service>.onrender.com` (or your custom domain),
- `API_VERSION_PREFIX` = your prefix, e.g. `v1_7b82`.

`LOG_LEVEL=INFO`, `LOG_FORMAT=json`, `LOG_FILE_ENABLED=false` are already set as
`value` entries in `render.yaml`.

Render secret env vars live under **Settings → Environment** on the service. Mark
sensitive ones as *Secret* so they are hidden after save.

## 3. Deploy

Click **Apply** on the Blueprint, or use

```bash
render blueprint apply
```

with the [Render CLI](https://render.com/docs/cli). The service builds the Docker
image and starts automatically. `healthCheckPath: /healthz` keeps the service
healthy (`/readyz` is a stricter check you can probe manually).

Investigate deploy logs at **Events → Logs** on the service; watch for MongoDB,
Redis, command sync, and bot menu setup.

## 4. Mini App URL

In BotFather, set the Mini App URL to `https://<your-service>.onrender.com` — the
same value as `WEB_APP_URL` (or your custom domain after you attach one).

## Free-tier notes

- Render free web services **sleep after 15 min of inactivity** — same keepalive need as
  Heroku (UptimeRobot hitting `/healthz` every ~5 min, or a paid instance).
- Render free tier cold-starts can take a while for this image; be patient on first
  request after sleep.

## Scaling and limits

- `maxShutdownDelaySeconds: 60` in the Blueprint gives in-flight requests time to finish.
- Keep **one instance** unless you are sure about Telegram-client duplication:
  multiple instances each run their own bot client and can conflict.
  If you must scale, ensure only one instance is the active bot (not currently supported
  out of the box — prefer staying at 1).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Build fails with `COPY pyproject.toml ...` not found | Build **context** must be `./backend` (Blueprint sets it; manual setups often miss it). |
| `Sync: false` variables empty | Fill them manually in service Settings → Environment; Blueprint never syncs secrets. |
| Health check failing | Confirm `/healthz` returns 200; check logs for a crashed bot (bad token, missing Redis). |
| Service sleeping | Free tier; add an uptime ping to `/healthz`. |
| 404 on `/api/...` | `API_VERSION_PREFIX` on backend must match frontend `VITE_API_PREFIX`. |

## References

- [Render Blueprint spec](https://render.com/docs/blueprint-spec)
- [Render Docker deployment](https://render.com/docs/docker)
- [Render health checks](https://render.com/docs/health-checks)