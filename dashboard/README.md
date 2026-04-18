# Chief of Staff dashboard

Vite + React + Tailwind. Data loads from the FastAPI app on your droplet (`api.py`) via `src/api/*.ts`.

**Full setup (droplet env, CORS, HTTPS, GitHub Pages):** see [`../docs/dashboard-setup.md`](../docs/dashboard-setup.md).

## Local development

```bash
cd dashboard
npm install
npm run dev
```

Configure **`VITE_API_URL`** (see `.env.development` or create `.env.local` to override). Sign in with the password from **`DASHBOARD_PASSWORD`** on the server — not stored in the frontend bundle.

Optional: `VITE_API_KEY` in `.env.local` matches `DASHBOARD_API_KEY` on the server for local scripting only.

## Production build

```bash
npm run build
```

Output: `dist/`. Preview with `npm run preview`.

## GitHub Pages

Set `base` in `vite.config.ts` to your repo path if needed (e.g. `/mason-agent/`). The API must list your Pages **origin** in `DASHBOARD_CORS_ORIGINS`. HTTPS Pages requires an **HTTPS** API URL in `VITE_API_URL` at build time.

## Architecture

- **Frontend:** Vite + React + Tailwind CSS v4 (`@tailwindcss/vite`).
- **Backend:** FastAPI in repo root `api.py`, same droplet as the Telegram agent.
