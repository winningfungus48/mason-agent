# Sync local token.json to the droplet and restart mason-api + mason-agent, then smoke-test /calendar/today.
# Run from anywhere; requires OpenSSH scp/ssh. You may be prompted for SSH/sudo passwords.
#
# Usage (from repo root):
#   .\scripts\sync-token-to-droplet.ps1 -SshTarget mason@203.0.113.50 -ApiBase "http://203.0.113.50:8000"
#
# ApiBase must match where the API listens (same host you use in the browser for the dashboard).

param(
    [Parameter(Mandatory = $true)]
    [string] $SshTarget,
    [Parameter(Mandatory = $true)]
    [string] $ApiBase,
    [string] $RemoteUser = "mason",
    [string] $RemotePath = "/home/mason/agent/token.json",
    [string] $DashboardPassword = "chief"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$token = Join-Path $repoRoot "token.json"
if (-not (Test-Path $token)) {
    Write-Error "Missing token.json at $token — run python scripts/google_reauth.py first."
}

$apiBase = $ApiBase.TrimEnd("/")

Write-Host "scp token.json -> ${SshTarget}:${RemotePath}"
& scp $token "${SshTarget}:${RemotePath}"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "sudo systemctl restart mason-api mason-agent"
& ssh $SshTarget "sudo systemctl restart mason-api mason-agent"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "POST /auth/login + GET /calendar/today"
$loginBody = @{ password = $DashboardPassword } | ConvertTo-Json
$tok = Invoke-RestMethod -Uri "$apiBase/auth/login" -Method POST -ContentType "application/json" -Body $loginBody -ErrorAction Stop
if (-not $tok.access_token) { Write-Error "Login failed — check ApiBase and DASHBOARD_PASSWORD on the server." }
$h = @{ Authorization = "Bearer $($tok.access_token)" }
$cal = Invoke-WebRequest -Uri "$apiBase/calendar/today" -Headers $h -UseBasicParsing -TimeoutSec 45
$snippet = $cal.Content.Substring(0, [Math]::Min(500, $cal.Content.Length))
Write-Host $snippet
if ($cal.Content -match "invalid_grant") { Write-Warning "Still seeing Google invalid_grant — token may not have landed or services need a moment." }
Write-Host "Done."
