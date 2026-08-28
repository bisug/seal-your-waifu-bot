# Deploying the Seal-Bot frontend to Cloudflare Pages

Cloudflare Pages hosts the **frontend only** (the React/Vite Telegram Mini App).
The Python backend **cannot** run on Cloudflare (Workers/Pages is serverless) —
see [Why not the backend?](#why-not-the-backend).

## Why not the backend?

Cloudflare Workers and Pages Functions are short-lived and request-scoped. The
backend needs a **persistent** process because it:

- starts Telegram bot clients (`TOKEN`/`SUB_TOKEN`) that long-poll for updates,
- runs background workers and schedulers,
- holds MongoDB and Redis client connections,
- serves WebSockets for live Mini App updates.

None of that works in a stateless edge function. **Keep the backend on a persistent
host** (Heroku, Render, Koyeb, Railway, or a VPS). Cloudflare Pages only serves the
built frontend.

> Note: the repo already contains `wrangler.toml` for Cloudflare Pages CI/CD; keep
> Pages settings aligned with it.

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

Set them as **Environment variables** in the Pages project:

```text
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

## 3. Create the Pages project

In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to Git**,
select the repo, then:

```text
Production branch: main
Root directory:    frontend
Build command:     npm run build
Build output directory: dist
```

Keep the root directory as `frontend` — do **not** set it to `dist`; Cloudflare
checks that directory before the build runs.

`frontend/wrangler.toml` (in the repo) matches these settings for CI-based deploys.

## 4. Deploy (dashboard or CLI)

Dashboard saves and builds automatically on push to `main`. Or use the CLI
(direct upload):

```bash
cd frontend
bun install --frozen-lockfile
bun run build
npx wrangler pages deploy dist --project-name seal-bot-frontend
```

For CI, use a **Build token** (not a global API token) with only
`Account > Cloudflare Pages > Edit` permission, plus these variables:

```text
CLOUDFLARE_ACCOUNT_ID=<your-cloudflare-account-id>
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

> Use `npx wrangler pages deploy`, never `npx wrangler deploy` — the latter is for
> Workers, not Pages.

The project URL looks like `https://seal-bot-frontend.pages.dev`.

## 5. Update the backend + BotFather

1. Set backend `WEB_APP_URL` to the Pages URL.
2. In BotFather, set the Mini App URL to the same Pages URL.
3. If you changed `VITE_API_URL` / `VITE_API_PREFIX`, rebuild and redeploy the frontend.

Custom domains: attach in **Pages → project → Custom domains**, then use that domain
in both BotFather and `WEB_APP_URL`.

## Troubleshooting

| Log text / symptom | Fix |
| --- | --- |
| `tsc: not found` | Keep the build command `npm run build`; that script installs dependencies before tsc/Vite run. |
| `Authentication error [code: 10000]` | Use a Build token with `Account > Cloudflare Pages > Edit` on the account that owns the project. |
| `Missing entry-point to Worker script` | Replace `npx wrangler deploy` with `npx wrangler pages deploy dist --project-name seal-bot-frontend`. |
| Blank page / API 404 | Check `VITE_API_PREFIX` matches backend `API_VERSION_PREFIX`; `VITE_API_URL` must not end in `/api/...`. |
| Mini App auth fails | `WEB_APP_URL` on the backend must equal the deployed Pages URL. |

## References

- [Cloudflare Pages — React framework guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-react-site/)
- [Wrangler Pages commands](https://developers.cloudflare.com/workers/wrangler/commands/pages/)
- [Pages direct upload + API tokens](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)