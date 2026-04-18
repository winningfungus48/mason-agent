"""
core/google_auth.py
-------------------
Single OAuth handler for all Google APIs.
Calendar, Tasks, and any future service (Gmail, Drive) all call get_service().
Token is shared across all services via token.json (written by Dashboard → Connect Google or scripts).

Interactive run_local_server() is not used here — headless servers cannot open a browser.
Use the dashboard OAuth flow (api.py) or scripts/google_reauth.py locally.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from core.config import GOOGLE_SCOPES, TOKEN_PATH


def _token_path_str() -> str:
    return TOKEN_PATH if isinstance(TOKEN_PATH, str) else str(TOKEN_PATH)


def get_service(api_name: str, api_version: str):
    """
    Authenticate and return a Google API service client.

    Usage:
        service = get_service("calendar", "v3")
        service = get_service("tasks", "v1")

    All services share one token.json. Adding a new Google service only
    requires adding its scope to GOOGLE_SCOPES in config.py.
    """
    tp = _token_path_str()
    creds = None

    if os.path.exists(tp):
        creds = Credentials.from_authorized_user_file(tp, GOOGLE_SCOPES)

    if not creds:
        raise RuntimeError(
            "Google is not connected. Open the dashboard and use “Connect Google”, "
            "or add a valid token.json (see docs)."
        )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(tp, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            except Exception as e:
                raise RuntimeError(
                    "Google token refresh failed (revoked or invalid). "
                    "Use Dashboard → Connect Google again."
                ) from e
        else:
            raise RuntimeError(
                "Google token is not valid. Use Dashboard → Connect Google, or add token.json."
            )

    return build(api_name, api_version, credentials=creds)
