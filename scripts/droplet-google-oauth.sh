#!/usr/bin/env bash
# Same idea as droplet-google-oauth.ps1 — from Mac/Linux/Git Bash.
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 mason@DROPLET_HOST"
  exit 1
fi
TARGET="$1"
REMOTE_DIR="${2:-/home/mason/agent}"
echo "Tunnel localhost:8765 -> ${TARGET}:127.0.0.1:8765 (background)"
ssh -N -L 8765:127.0.0.1:8765 "$TARGET" &
TUNNEL_PID=$!
sleep 2
cleanup() { kill "$TUNNEL_PID" 2>/dev/null || true; }
trap cleanup EXIT
echo "Running google_reauth.py --droplet on server..."
ssh "$TARGET" "bash -lc 'cd $REMOTE_DIR && source venv/bin/activate && python scripts/google_reauth.py --droplet'"
echo "Restarting services..."
ssh "$TARGET" "sudo systemctl restart mason-api mason-agent"
echo "Done."
