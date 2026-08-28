# Deploying the Seal-Bot frontend to Vercel

Vercel hosts the **frontend only** (the React/Vite Telegram Mini App). The Python
backend **cannot** run on Vercel — see [Why not the backend?](#why-not-the-backend).

## Why not the backend?

Vercel functions are serverless: short-lived, request-scoped, no long-running
process. The backend needs a **persistent** process because it:

- starts Telegram bot clients (`TOKEN`/`SUB_TOKEN`) that long-poll for updates,
- runs background workers and schedulers,
- holds MongoDB and Redis client connections,
- serves WebSockets for live Mini App updates.

None of that works in a stateless function. **Keep the backend on a persistent
host** (Heroku, Render, Koyeb, Railway, or a VPS). Vercel only serves the built
frontend.

## 1. Deploy the backend first

Pick a persistent host and follow its guide:

- [Heroku](heroku.md)
- [Render](render.md)
- [Koyeb](koyeb.md)

Note its public HTTPS origin. You need the backend **and** MongoDB/Redis reachable.

## 2. Point the frontend at the backend

The frontend reads two build-time variables (from `frontend/`):

| Variable | Purpose | Example |
| --- | --- | --- |
| `VITE_API_URL` | Backend origin (no `/api/...` suffix) | `https://seal-backend.onrender.com` |
| `VITE_API_PREFIX` | Must equal backend `API_VERSION_PREFIX` | `v1_7b82` |

Create them under **Project → Settings → Environment Variables** in Vercel, for the
**Production** environment (and Preview if you deploy branches).

## 3. Configure and deploy

Settings on the Vercel project (Import from Git, repo = this monorepo):

```text
Root Directory: frontend
Framework Preset: Vite
Install Command:  bun install --frozen-lockfile
Build Command:    bun run build
Output Directory: dist
```

Or from the CLI:

```bash
cd frontend
bun install --frozen-lockfile
vercel
vercel --prod
```

`frontend/vercel.json` handles SPA routing:

```json
{
  "buildCommand": "bun run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

That rewrites every path to `index.html` so direct routes (e.g. `/profile`) work;
the Vite build outputs hashed assets under `dist/assets`, which are served as-is.

## 4. Update the backend + BotFather

1. Set backend `WEB_APP_URL` to the Vercel URL (e.g. `https://seal-frontend.vercel.app`).
2. In BotFather, set the Mini App URL to the same Vercel URL.
3. If you changed `VITE_API_URL` or `VITE_API_PREFIX`, **rebuild the frontend** and
   redeploy (Vercel redeploys on new commits automatically).

## Notes

- `VITE_*` values are public browser values — no secrets there.
- `@vercel/speed-insights` is already a dependency and works out of the box.
- For a custom domain, attach it in **Project → Domains**; use the same domain in
  BotFather and in `WEB_APP_URL`.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Blank page / API 404 | `VITE_API_PREFIX` mismatch with backend `API_VERSION_PREFIX`, or `VITE_API_URL` ends with `/api/...` (remove it). |
| Direct route 404 | Ensure `vercel.json` rewrites are present (this repo ships them). |
| Auth fails in the Mini App | `WEB_APP_URL` in backend must equal the deployed Vercel URL; re-check BotFather. |
| Build uses npm instead of bun | Set Install Command to `bun install --frozen-lockfile` (Bun is preinstalled on Vercel). |

## References

- [Vercel Vite deployment](https://vercel.com/docs/frameworks/frontend/vite)
- [Vercel framework preset / env vars](https://vercel.com/docs/projects/environment-variables)
- [Vercel CLI](https://vercel.com/docs/cli)