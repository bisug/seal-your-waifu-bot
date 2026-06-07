# Seal WebApp Frontend

React 19 + Vite 8 Telegram Mini App frontend for Seal-Bot.

## Commands

```sh
bun install
bun run dev
bun run lint
bun run type-check
bun run build
bun run deploy
bun run deploy:cloudflare
```

## Frontend-only hosting

When deploying only this frontend to Vercel, Netlify, or Cloudflare Pages, configure:

```sh
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

Use `frontend` as the Cloudflare project root directory, `bun run build` as the build command, `dist` as the output directory, and leave Deploy command empty for normal Cloudflare Pages Git deployments. Do not set the root directory to `dist`; Cloudflare checks that directory before the build runs. The backend must run separately on Heroku, Render, Railway, a VPS, or another host that supports a persistent Python process.

For Cloudflare Pages, do not use `npx wrangler deploy`; that command is for Workers. Use the dashboard build settings above, or direct upload with:

```sh
bun run deploy:cloudflare
```

Only use a deploy command for manual/direct upload workflows outside the normal Cloudflare Pages Git build. In that case, after the app has already been built, use:

```sh
bun run deploy
```

## Tooling

- Stable TypeScript via `tsc`
- ESLint flat config with TypeScript, React Hooks, and React Refresh rules
- Tailwind CSS v4 through `@tailwindcss/vite`

The production build is copied into `Grabber/static` by the root Dockerfile.
