#!/usr/bin/env python3
"""
Re-run Google OAuth (browser) and write token.json using GOOGLE_SCOPES from core/config.

Run on a machine WITH a desktop browser — not on a headless droplet.
Requires credentials.json in the repo root (same folder as api.py).

Usage (from repo root):
  python scripts/google_reauth.py

Then copy the new token.json to the droplet:
  scp token.json mason@YOUR_DROPLET:/home/mason/agent/

Back up the old token on the droplet first if you want a rollback.
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CREDS = os.path.join(REPO_ROOT, "credentials.json")


def main() -> int:
    if not os.path.isfile(CREDS):
        print(f"Missing {CREDS} — add OAuth client JSON from Google Cloud (Desktop app).", file=sys.stderr)
        return 1
    from core.google_auth import get_service

    print("Opening browser for Google sign-in (Calendar + Tasks scopes)...")
    get_service("calendar", "v3")
    print("Calendar: OK")
    get_service("tasks", "v1")
    print("Tasks: OK")
    print(f"Wrote token.json under {REPO_ROOT}")
    print("Copy to droplet: scp token.json mason@YOUR_HOST:/home/mason/agent/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
