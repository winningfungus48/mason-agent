#!/usr/bin/env python3
"""Merge scripts/github-pages-origin.txt into DASHBOARD_CORS_ORIGINS in .env (idempotent).

Run from deploy.sh after git pull so the droplet picks up the Pages URL without manual .env edits.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENV_PATH = REPO / ".env"
ORIGIN_PATH = Path(__file__).resolve().parent / "github-pages-origin.txt"


def _first_origin() -> str | None:
    if not ORIGIN_PATH.exists():
        return None
    for line in ORIGIN_PATH.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        return s.rstrip("/")
    return None


def main() -> int:
    extra = _first_origin()
    if not extra:
        return 0
    if not ENV_PATH.exists():
        print(f"merge_github_pages_cors: no {ENV_PATH}, skip", file=sys.stderr)
        return 0

    text = ENV_PATH.read_text(encoding="utf-8")
    ends_with_nl = text.endswith("\n")
    out_lines: list[str] = []
    found = False
    for line in text.splitlines():
        if line.startswith("DASHBOARD_CORS_ORIGINS="):
            found = True
            val = line.split("=", 1)[1].strip()
            parts = [p.strip().rstrip("/") for p in val.split(",") if p.strip()]
            if extra not in parts:
                parts.append(extra)
            out_lines.append("DASHBOARD_CORS_ORIGINS=" + ",".join(parts))
        else:
            out_lines.append(line)
    if not found:
        out_lines.append("DASHBOARD_CORS_ORIGINS=" + extra)

    new_text = "\n".join(out_lines)
    if ends_with_nl or not new_text:
        new_text += "\n"
    ENV_PATH.write_text(new_text, encoding="utf-8")
    print(f"merge_github_pages_cors: ensured {extra!r} in DASHBOARD_CORS_ORIGINS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
