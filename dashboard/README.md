# Chief of Staff dashboard

Static React dashboard for the personal AI agent. Data is mocked in `src/constants/mockData.ts`; each feature area loads through `src/api/*.ts` so you can swap in real `fetch` calls when the FastAPI layer on the droplet is ready.

## Local development

```bash
cd dashboard
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`).

## Password gate

The unlock password is hardcoded at the top of `src/components/PasswordGate.tsx` (`DASHBOARD_PASSWORD`). Change it there. Successful login is stored in `sessionStorage` so refreshes stay signed in until the tab session ends.

## Environment (future API)

Create `.env.local` (gitignored) when the backend exists:

```bash
VITE_API_BASE_URL=https://104.131.39.150:8443
```

`src/constants/apiConfig.ts` exposes `API_BASE_URL` from `import.meta.env.VITE_API_BASE_URL`. Individual `src/api/*` modules can use it for `fetch` without touching UI components.

## Production build

```bash
npm run build
```

Output is in `dist/`. Preview locally with `npm run preview`.

## GitHub Pages (or static hosting)

1. Set the Vite `base` option to your repo path if the site is not at the domain root, e.g. in `vite.config.ts`:

   ```ts
   export default defineConfig({
     base: '/mason-agent/',
     plugins: [react(), tailwindcss()],
   })
   ```

   Use `/` if you use a custom domain or user/org site at root.

2. Build and deploy the `dist/` folder (GitHub Actions, `gh-pages` branch, or any static host).

3. CORS: the FastAPI app on the droplet must allow your static origin when you switch from mocks to real requests.

## Architecture notes

- **Frontend:** Vite + React + Tailwind CSS v4 (`@tailwindcss/vite`).
- **Backend (later):** FastAPI on the droplet, importing existing `agents/` and `core/` code; dashboard calls `https://<host>:<port>/...` (TLS and port are your ops choice; the skeleton uses env-based base URL only).
