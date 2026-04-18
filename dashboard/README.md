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

## GitHub Pages (production)

Deploys are **manual** — pushing to `main` does not update the live site. After secrets and CORS are set up, run from repo root: **`scripts/deploy-github-pages.ps1`** (Windows) or **`scripts/deploy-github-pages.sh`** (macOS/Linux), or **Actions → Run workflow**. See [`../docs/dashboard-setup.md`](../docs/dashboard-setup.md) Phase 7.

The workflow builds with `--base=/mason-agent/`. **`VITE_API_URL`** must be an **HTTPS** API URL via GitHub Actions secrets. The dashboard password stays **`DASHBOARD_PASSWORD`** on the server only — never in `VITE_*` or the repo.

## Architecture

- **Frontend:** Vite + React + Tailwind CSS v4 (`@tailwindcss/vite`).
- **Backend:** FastAPI in repo root `api.py`, same droplet as the Telegram agent.
