#!/usr/bin/env python3
"""
Refresh Google OAuth token.json (Calendar + Tasks scopes from core/config).

  Default (laptop with a browser): opens a local server and your browser.
  Droplet (headless): use --droplet plus an SSH tunnel from your laptop (see below).

Requires credentials.json in the repo root. Writes token.json in the repo root.
"""
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CREDS = os.path.join(REPO_ROOT, "credentials.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Google OAuth re-auth for Mason agent")
    parser.add_argument(
        "--droplet",
        action="store_true",
        help="Listen on 127.0.0.1:8765 for OAuth redirect; use with SSH tunnel from your PC (no scp).",
    )
    args = parser.parse_args()

    if not os.path.isfile(CREDS):
        print(f"Missing {CREDS}", file=sys.stderr)
        print(
            "  On the droplet, credentials.json should already be at /home/mason/agent/credentials.json",
            file=sys.stderr,
        )
        return 1

    from core.config import GOOGLE_SCOPES, TOKEN_PATH
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDS, GOOGLE_SCOPES)

    if args.droplet:
        print(
            "\n=== Droplet mode ===\n"
            "On your PC (separate terminal), keep this tunnel open:\n"
            "  ssh -N -L 8765:127.0.0.1:8765 mason@YOUR_DROPLET\n"
            "Then open the URL printed below in your PC browser and sign in.\n"
            "Google will redirect to http://localhost:8765/ — the tunnel sends it to this machine.\n",
            flush=True,
        )
        creds = flow.run_local_server(
            host="localhost",
            bind_addr="127.0.0.1",
            port=8765,
            open_browser=False,
            authorization_prompt_message="Open this URL in your PC browser (with SSH tunnel active):\n{url}\n",
            access_type="offline",
            prompt="consent",
        )
    else:
        print("Opening browser for Google sign-in (Calendar + Tasks scopes)...", flush=True)
        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
        )

    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    # Verify APIs load (uses new token; no second browser if token is fresh)
    from core.google_auth import get_service

    get_service("calendar", "v3")
    print("Calendar: OK", flush=True)
    get_service("tasks", "v1")
    print("Tasks: OK", flush=True)
    print(f"Wrote {TOKEN_PATH}", flush=True)
    if not args.droplet:
        print("For the droplet: run with --droplet over SSH tunnel, or scp token.json to the server.", flush=True)
    else:
        print("Restart services: sudo systemctl restart mason-api mason-agent", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
