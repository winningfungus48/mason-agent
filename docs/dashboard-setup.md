# Dashboard + API setup (step-by-step)

Follow in order. Your droplet user is `mason`, project path `/home/mason/agent`, unless you changed that.

**New to SSH?** Read **[ssh-beginner.md](ssh-beginner.md)** first (open terminal, one `ssh` command, optional shortcut).

### Development vs production (summary)

| | **Local dev** | **Production (GitHub Pages)** |
|--|----------------|--------------------------------|
| **Goal** | Fast UI iteration | Same app for mobile/desktop over HTTPS |
| **Run** | `cd dashboard` → `npm run dev` (Vite opens the browser) | Build + deploy only when **you** trigger it (not on every `git push`) |
| **API URL** | `dashboard/.env.development` or `.env.local` → e.g. `http://127.0.0.1:8000` or your tunnel | Set as **`VITE_API_URL`** in **GitHub Actions secrets** (must be **HTTPS** so the HTTPS Page can call it) |
| **Password** | Type the same value as **`DASHBOARD_PASSWORD`** on the server — **never** commit it or put it in `VITE_*` | Same: server-only secret; static JS does not contain the password |
| **Data access** | After login, API returns data | Same: only **logged-in** clients get data; the HTML/JS bundle is still publicly downloadable (normal for SPAs) |

---

## Phase 1 — Droplet: Python dependencies

SSH into the droplet, then:

```bash
cd /home/mason/agent
source venv/bin/activate
pip install -r requirements.txt
```

Confirm `itsdangerous` installed (used for signed login tokens).

---

## Phase 2 — Droplet: environment variables

Edit `/home/mason/agent/.env` (same file the Telegram bot and `mason-api.service` already load).

**Add or set these** (keep existing keys like `TELEGRAM_BOT_TOKEN`, Google paths, etc.):

| Variable | Purpose |
|----------|---------|
| `SESSION_SECRET` | Random secret for signing Bearer tokens. Generate: `openssl rand -hex 32` |
| `DASHBOARD_PASSWORD` | Password you type in the web UI (strong, unique) |
| `DASHBOARD_CORS_ORIGINS` | Comma-separated browser origins allowed to call the API. Include local Vite **and** your GitHub Pages URL (see below). No trailing slashes on origins is fine; the API normalizes. Example: `https://YOURUSER.github.io,http://localhost:5173,http://127.0.0.1:5173` |
| `DASHBOARD_API_KEY` | *(Optional)* For curl/scripts only — **not** required for the React app after password login |

**Do not** put `SESSION_SECRET` or `DASHBOARD_PASSWORD` in the GitHub repo or in the frontend.

See `api.env.example` in the repo root for a paste-friendly template.

---

## Phase 3 — Droplet: CORS and GitHub Pages

1. Replace `YOURUSER` / repo name in `DASHBOARD_CORS_ORIGINS` with your real GitHub Pages origin, e.g. `https://winningfungus48.github.io` if the site is at the user root, or `https://winningfungus48.github.io/mason-agent/` — use the **origin only** (scheme + host, and path if the app is not at repo root — for `base: '/mason-agent/'` the origin is still `https://user.github.io`; path is not part of CORS origin).  
   **Correct:** `https://winningfungus48.github.io`  
   **Wrong:** trailing path on origin for standard CORS (use the site’s origin as the browser sends it).

2. **HTTPS:** GitHub Pages is served over **HTTPS**. Browsers **block** `fetch` from HTTPS pages to an **HTTP** API (mixed content). For production you must serve the API over **HTTPS** (e.g. nginx or Caddy on the droplet with Let’s Encrypt). Until then, test from **http://localhost** only, or use a tunnel for quick tests.

---

## Phase 4 — Droplet: firewall

Ensure port **8000** (or whatever port `mason-api` uses) is allowed:

```bash
sudo ufw allow 8000/tcp
sudo ufw status
```

Also open the same port in the **DigitalOcean cloud firewall** if you use one.

---

## Phase 5 — Droplet: systemd

Install or refresh the unit (paths assume `/home/mason/agent`):

```bash
sudo cp /home/mason/agent/mason-api.service /etc/systemd/system/mason-api.service
sudo systemctl daemon-reload
sudo systemctl enable mason-api
sudo systemctl restart mason-api
sudo systemctl status mason-api
```

Quick checks:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"YOUR_DASHBOARD_PASSWORD"}'
```

The second command should return JSON with `access_token`.

---

## Phase 6 — Laptop: dashboard env

1. `cd dashboard`
2. Ensure `VITE_API_URL` points at your API (in dev, `.env.development` is committed for convenience; override in `.env.local` if needed).  
   - HTTP droplet IP: `http://YOUR_IP:8000` — OK for **local** dev from `http://localhost`.  
   - Production: **`https://`** your API hostname once TLS is set up.

3. `npm install` then `npm run dev`

4. Open the app, unlock with **`DASHBOARD_PASSWORD`** (same as on the server).

Optional: set `VITE_API_KEY` in `.env.local` only for local automation; the UI uses password + Bearer token by default.

---

## Phase 7 — Publish the dashboard to GitHub Pages (manual)

Pushing to `main` **does not** deploy the site. You choose when production updates.

1. **One-time — GitHub repository secrets** (Settings → Secrets and variables → Actions):  
   - **`VITE_API_URL`** — production API base URL, **HTTPS**, **no trailing slash** (e.g. `https://your-api.example.com` or your **HTTPS** ngrok URL). This is baked into the built JS; it is **not** a password.  
   - **`VITE_API_KEY`** — optional; only if you use `DASHBOARD_API_KEY` for automation. Omit unless you need it.

2. **CORS on the droplet** — `DASHBOARD_CORS_ORIGINS` must include `https://YOURUSER.github.io`. Running **`./deploy.sh`** on the droplet (after `git pull`) runs `scripts/merge_github_pages_cors.py` to merge the origin from `scripts/github-pages-origin.txt` into `.env`, then restarts services.

3. **Deploy command** (after your changes are on `main`): from the repo root, run **one** of:  
   - **Windows (PowerShell):** `.\scripts\deploy-github-pages.ps1`  
   - **macOS / Linux / Git Bash:** `./scripts/deploy-github-pages.sh`  
   - Or: GitHub → **Actions** → **Deploy Dashboard to GitHub Pages** → **Run workflow**

   Requires [GitHub CLI](https://cli.github.com/) (`gh`) installed and `gh auth login` for the scripts.

4. Watch the workflow finish, then open your Pages URL (e.g. `https://YOURUSER.github.io/mason-agent/`).

**Local production-like build (optional):** `cd dashboard` → `npm run build -- --base=/mason-agent/` with `VITE_API_URL` set in the environment — same as CI.

---

## Phase 8 — After it works

- Rotate `DASHBOARD_PASSWORD` and `SESSION_SECRET` if they were ever exposed.
- Use `./deploy.sh` on the droplet after `git pull`. It runs `scripts/merge_github_pages_cors.py`, which adds the origin from `scripts/github-pages-origin.txt` to `DASHBOARD_CORS_ORIGINS` in `.env` (edit that file if you fork or change your Pages URL), then restarts `mason-agent` and `mason-api`.
- Next: module-by-module features (chores, meal plan, etc.) on top of the same API pattern.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| CORS error in browser | `DASHBOARD_CORS_ORIGINS` includes your exact site origin (e.g. `https://YOURUSER.github.io`); restart `mason-api` |
| CORS only when using **ngrok** free URL | ngrok’s warning page has no CORS headers. The dashboard sends `ngrok-skip-browser-warning` when `VITE_API_URL` is an ngrok host. You still must list the Pages origin in `DASHBOARD_CORS_ORIGINS`. |
| Mixed content blocked | API must be HTTPS when the site is HTTPS |
| 401 on every request | Log in again; token in `sessionStorage`; or set `VITE_API_KEY` for dev scripts |
| 503 on `/auth/login` | `SESSION_SECRET` and `DASHBOARD_PASSWORD` set in droplet `.env` |
