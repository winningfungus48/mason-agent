"""
core/google_auth.py
-------------------
Single OAuth handler for all Google APIs.
Calendar, Tasks, and any future service (Gmail, Drive) all call get_service().
Token is shared across all services via token.json.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from core.config import TOKEN_PATH, CREDS_PATH, GOOGLE_SCOPES


def get_service(api_name: str, api_version: str):
    """
    Authenticate and return a Google API service client.

    Usage:
        service = get_service("calendar", "v3")
        service = get_service("tasks", "v1")

    All services share one token.json. Adding a new Google service only
    requires adding its scope to GOOGLE_SCOPES in config.py.
    """
    creds = None

    if TOKEN_PATH.exists() if hasattr(TOKEN_PATH, 'exists') else __import__('os').path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build(api_name, api_version, credentials=creds)
