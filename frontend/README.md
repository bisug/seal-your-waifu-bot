# Seal WebApp Frontend

React 19 + Vite 8 Telegram Mini App frontend for Seal-Bot.

## Commands

```sh
bun install
bun run dev
bun run lint
bun run type-check
bun run build
```

## Frontend-only hosting

When deploying only this frontend to Vercel, Netlify, or Cloudflare Pages, configure:

```sh
VITE_API_URL=https://your-backend.example.com
VITE_API_PREFIX=v1_7b82
```

Use `bun run build` as the build command and `dist` as the output directory. The backend must run separately on Heroku, Render, Railway, a VPS, or another host that supports a persistent Python process.

## Tooling

- Stable TypeScript via `tsc`
- ESLint flat config with TypeScript, React Hooks, and React Refresh rules
- Tailwind CSS v4 through `@tailwindcss/vite`

The production build is copied into `Grabber/static` by the root Dockerfile.
