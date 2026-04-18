#!/usr/bin/env bash
# Triggers the GitHub Actions workflow that builds and deploys the dashboard to GitHub Pages.
# Requires: GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
# Repo secrets must include VITE_API_URL (HTTPS API base URL for production; no trailing slash).
set -euo pipefail
cd "$(dirname "$0")/.."
exec gh workflow run "Deploy Dashboard to GitHub Pages" --ref main
