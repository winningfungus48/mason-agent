# Run Google OAuth ON THE DROPLET while you complete sign-in in a PC browser (via SSH tunnel).
# No scp of token.json — token is written directly on the server.
#
# Prerequisites: OpenSSH client, SSH access to droplet, credentials.json already on droplet at /home/mason/agent/
#
# Usage:
#   .\scripts\droplet-google-oauth.ps1 -DropletHost YOUR_PUBLIC_IPV4
#   .\scripts\droplet-google-oauth.ps1 -DropletHost YOUR_PUBLIC_IPV4 -SshPort 2222
#
# Use the **current** public IPv4 from DigitalOcean → Droplets → your droplet (copy from the panel).
# The IP in docs (e.g. 104.131.x.x) is only an example — yours may differ.
#
# Steps: starts a background SSH tunnel (local 8765 -> droplet 8765), runs google_reauth.py --droplet on the droplet,
# then restarts services. Keep this window open until OAuth finishes.

param(
    [Parameter(Mandatory = $true)]
    [string] $DropletHost,
    [int] $SshPort = 22,
    [string] $RemoteUser = "mason",
    [string] $RemoteDir = "/home/mason/agent"
)

$ErrorActionPreference = "Stop"
$target = if ($DropletHost -match "@") { $DropletHost } else { "${RemoteUser}@${DropletHost}" }

function Test-SshReachable {
    param([string]$T, [int]$Port)
    $a = $T -split "@"
    $hostOnly = if ($a.Length -gt 1) { $a[-1] } else { $T }
    Write-Host "Checking TCP $hostOnly`:$Port (5s timeout)..."
    $r = Test-NetConnection -ComputerName $hostOnly -Port $Port -WarningAction SilentlyContinue
    return $r.TcpTestSucceeded
}

if (-not (Test-SshReachable -T $target -Port $SshPort)) {
    Write-Host @"

SSH port $SshPort is not reachable from this PC to $target.

Fix (pick what applies):
  1. DigitalOcean → Droplets → copy the **current Public IPv4** (IPs can change if you recreated the droplet).
  2. Cloud firewall / droplet firewall: allow **inbound TCP 22** (or your custom SSH port) from **your home IP** or **0.0.0.0/0** for testing.
  3. Confirm the droplet is **powered on**.
  4. From this PC, run:  ssh -p $SshPort $target
     If that fails, fix SSH before re-running this script.

"@
    throw "SSH unreachable"
}

$sshCommon = @("-o", "ConnectTimeout=15")
if ($SshPort -ne 22) { $sshCommon += "-p", "$SshPort" }

Write-Host "Starting SSH tunnel: localhost:8765 -> ${target}:127.0.0.1:8765"
$tunnelArgs = $sshCommon + @("-N", "-L", "8765:127.0.0.1:8765", $target)
$tunnel = Start-Process -FilePath "ssh" -ArgumentList $tunnelArgs -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

try {
    Write-Host "Running google_reauth.py --droplet on server (open the printed URL in your PC browser)..."
    $runRemote = "bash -lc 'cd $RemoteDir && source venv/bin/activate && python scripts/google_reauth.py --droplet'"
    & ssh @sshCommon $target $runRemote
    if ($LASTEXITCODE -ne 0) { throw "Remote script failed with exit $LASTEXITCODE" }
    Write-Host "`nRestarting services on droplet..."
    & ssh @sshCommon $target "sudo systemctl restart mason-api mason-agent"
    Write-Host "Done. On the droplet, test calendar: curl with Bearer token to http://127.0.0.1:8000/calendar/today"
}
finally {
    if (-not $tunnel.HasExited) {
        Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    }
}
