# Seal WebApp Frontend

React 19 + Vite 8 Telegram Mini App frontend for Seal-Bot.

## Commands

```sh
bun install
bun run dev
bun run lint
bun run type-check
bun run build
bun run build:cloudflare
bun run deploy
bun run deploy:cloudflare
```

## Frontend-only hosting

When deploying only this frontend to Vercel, Netlify, or Cloudflare Pages, configure:

```sh
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

Use `frontend` as the Cloudflare project root directory, `bun run build:cloudflare` as the build command, `dist` as the output directory, and the Pages deploy command below if Cloudflare's build UI requires a Deploy command. `build:cloudflare` runs `bun install --frozen-lockfile` before the Vite build, which avoids `tsc: command not found` when Cloudflare skips dependency installation. Do not set the root directory to `dist`; Cloudflare checks that directory before the build runs. The backend must run separately on Heroku, Render, Railway, a VPS, or another host that supports a persistent Python process.

For Cloudflare Pages, do not use `npx wrangler deploy`; that command is for Workers. Use this deploy command in Cloudflare's build settings:

```sh
npx wrangler pages deploy dist --project-name seal-bot-frontend
```

The selected Cloudflare Build token must have `Account > Cloudflare Pages > Edit` permission. If the Pages project name is different, replace `seal-bot-frontend`.

For local or external direct upload, use:

```sh
bun run deploy:cloudflare
```

After the app has already been built, use:

```sh
bun run deploy
```

## Tooling

- Stable TypeScript via `tsc`
- ESLint flat config with TypeScript, React Hooks, and React Refresh rules
- Tailwind CSS v4 through `@tailwindcss/vite`

The production build is copied into `Grabber/static` by the root Dockerfile.
