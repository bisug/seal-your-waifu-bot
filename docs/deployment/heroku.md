# Deploying Seal-Bot to Heroku

Heroku runs the backend as a container using the existing `heroku.yml`, with
frontend served from the same dyno. This is the original deployment target of the
project (the `heroku.yml` in the repo root already points at `backend/Dockerfile`).

## Requirements

- A Heroku account and the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) (`heroku --version`)
- A MongoDB (Atlas) connection string
- A Redis connection string (e.g. Upstash, Memurai, Scaledrone)
- The env values from [Env variables](README.md#env-variables-all-platforms); especially `TOKEN`, `API_ID`, `API_HASH`, `MONGO_URL`.

## 1. Create the app (container stack)

The included `heroku.yml` uses the **container** stack:

```bash
heroku login
heroku create your-app-name --stack container
heroku stack:set container
```

If you already created the app with the default (buildpack) stack, `heroku stack:set container`
switches it. Only the container stack uses `heroku.yml`.

## 2. Set environment variables

Never push a `.env` to Heroku. Set each value with `heroku config:set` (one click copies the whole command):

```bash
heroku config:set TOKEN=REDACTED \
  SUB_TOKEN=REDACTED \
  API_ID=1234567 \
  API_HASH=REDACTED \
  MONGO_URL=REDACTED \
  REDIS_URL=REDACTED \
  OWNER_ID=123456789 \
  SUDO_USERS=123456789,987654321 \
  MAIN_GROUP_ID=-1001234567890 \
  GALLERY_CHANNEL_ID=-1001234567891 \
  LOG_GROUP_ID=-1001234567892 \
  WEB_APP_URL=https://your-app-name.herokuapp.com \
  MINI_APP_SHORT_NAME=app \
  API_VERSION_PREFIX=v1_7b82 \
  LOG_LEVEL=INFO \
  LOG_FORMAT=json \
  LOG_FILE_ENABLED=false
```

`heroku.yml` also supports the Heroku dashboard *Settings → Config Vars*; both work.

> `WEB_APP_URL` must be the public HTTPS origin of the Mini App. When the frontend is
> served from this same dyno, that is `https://<your-app-name>.herokuapp.com`.

## 3. Push and deploy

```bash
git push heroku main
```

Heroku builds the container defined in `heroku.yml` (build context `backend/`) and
starts `uvicorn backend.webapp.main:app --host 0.0.0.0 --port $PORT --workers 1`.

Check the logs while the dyno boots:

```bash
heroku logs --tail
```

Confirm readiness: `/healthz` returns `{"status":"ok"}` and `/readyz` reports
`mongo`, `redis`, and `bots` status.

## 4. Attach the Mini App URL in BotFather

In BotFather, set the Mini App URL of your bot to `https://your-app-name.herokuapp.com`
(identical to `WEB_APP_URL`).

## 5. Keepalive (important)

Heroku **stops dynos after ~30 min of inactivity** on free and hobby plans. The bot
must stay awake. Options:

```bash
heroku features:enable dyno-metadata
```

The simplest durable fix is a paid dyno or a third-party uptime ping
(e.g. UptimeRobot hitting `/healthz` every 5–10 minutes). A custom domain also
avoids cold starts on sleep cycles.

## Scaling

- Heroku dynos scale by count; **do not** scale web to more than 1 worker — duplicate
  Telegram clients will fight over updates.
- If you separate frontend hosting later, set `WEB_APP_URL` to that URL and rebuild the frontend.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Error: image ... does not exist` / stack mismatch | Confirm `heroku stack:set container` before pushing. |
| Dyno restarts after ~30 min idle | Enable a keepalive ping or a paid dyno (see step 5). |
| `ModuleNotFoundError` on build | Ensure `heroku.yml` build path and `backend/Dockerfile` context match (they do in this repo). |
| 404 on Mini App routes | The backend serves the built frontend; if you host the frontend separately, point `WEB_APP_URL` there and rebuild it. |

## References

- [Heroku container registry and runtime](https://devcenter.heroku.com/articles/container-registry-and-runtime)
- [Heroku `app.json` / declarative configuration](https://devcenter.heroku.com/articles/app-json-schema)
- [Heroku dyno sleeping](https://devcenter.heroku.com/articles/free-dyno-hours#dyno-sleeping)