# Triggers the GitHub Actions workflow that builds and deploys the dashboard to GitHub Pages.
# Requires: GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
# Repo secrets must include VITE_API_URL (HTTPS API base URL for production; no trailing slash).
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
gh workflow run "Deploy Dashboard to GitHub Pages" --ref main
Write-Host "Workflow started. Open the Actions tab on GitHub to watch the run."
