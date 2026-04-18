# Run Google OAuth ON THE DROPLET while you complete sign-in in a PC browser (via SSH tunnel).
# No scp of token.json — token is written directly on the server.
#
# Prerequisites: OpenSSH client, SSH access to droplet, credentials.json already on droplet at /home/mason/agent/
#
# Usage:
#   .\scripts\droplet-google-oauth.ps1 -DropletHost 104.131.x.x
#
# Steps: starts a background SSH tunnel (local 8765 -> droplet 8765), runs google_reauth.py --droplet on the droplet,
# then reminds you to restart services. Keep this window open until OAuth finishes.

param(
    [Parameter(Mandatory = $true)]
    [string] $DropletHost,
    [string] $RemoteUser = "mason",
    [string] $RemoteDir = "/home/mason/agent"
)

$ErrorActionPreference = "Stop"
$target = if ($DropletHost -match "@") { $DropletHost } else { "${RemoteUser}@${DropletHost}" }

Write-Host "Starting SSH tunnel: localhost:8765 -> ${target}:127.0.0.1:8765"
$tunnel = Start-Process -FilePath "ssh" -ArgumentList @("-N", "-L", "8765:127.0.0.1:8765", $target) -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

try {
    Write-Host "Running google_reauth.py --droplet on server (open the printed URL in your PC browser)..."
    ssh $target "bash -lc 'cd $RemoteDir && source venv/bin/activate && python scripts/google_reauth.py --droplet'"
    if ($LASTEXITCODE -ne 0) { throw "Remote script failed with exit $LASTEXITCODE" }
    Write-Host "`nRestarting services on droplet..."
    ssh $target "sudo systemctl restart mason-api mason-agent"
    Write-Host "Done. On the droplet, test calendar: curl with Bearer token to http://127.0.0.1:8000/calendar/today"
}
finally {
    if (-not $tunnel.HasExited) {
        Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    }
}
