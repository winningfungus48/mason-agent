#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Ensure GitHub Pages origin is in DASHBOARD_CORS_ORIGINS (see scripts/github-pages-origin.txt).
python3 scripts/merge_github_pages_cors.py
# Restart Mason agent (Telegram) and FastAPI dashboard API after deploy.
sudo systemctl restart mason-agent
sudo systemctl restart mason-api
