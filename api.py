"""
FastAPI dashboard API for Mason's agent.
Imports existing agents — no duplicated business logic.
Run: uvicorn api:app --host 0.0.0.0 --port 8000

Auth (no third-party IdP):
  - POST /auth/login with { "password": "<DASHBOARD_PASSWORD>" } → Bearer token (signed, itsdangerous).
  - Protected routes: Authorization: Bearer <token> OR X-API-Key: <DASHBOARD_API_KEY> (optional automation).
  - Env: SESSION_SECRET, DASHBOARD_PASSWORD, DASHBOARD_CORS_ORIGINS (comma-separated). Optional: DASHBOARD_API_KEY.
  - Google: credentials.json + redirect /auth/google/callback (see PUBLIC_BASE_URL). "Connect Google" writes token.json.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import secrets
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote

import zoneinfo
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

from agent import run_agent_conversational
from agents import briefing_agent, chores_agent, habits_agent, lists_agent, tasks_agent
from core.config import (
    CREDS_PATH,
    DOCUMENTS_DIR,
    GROCERY_CATEGORIES,
    GOOGLE_SCOPES,
    HABITS,
    HABIT_FILE,
    LISTS,
    QUARTERLY_MONTHS,
    ANNUAL_MONTHS,
    TIMEZONE,
    TOKEN_PATH,
    WEEKDAY_TAGS,
)

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
api_logger = logging.getLogger("mason_api")
api_logger.setLevel(logging.INFO)
_fh = logging.FileHandler(LOG_DIR / "api.log", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
if not api_logger.handlers:
    api_logger.addHandler(_fh)

API_KEY = os.getenv("DASHBOARD_API_KEY", "")
# Signed Bearer tokens for the dashboard (itsdangerous). Required for password login.
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
# Plain-text dashboard password (keep long & random). Validated only on the server.
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
TOKEN_MAX_AGE_SECONDS = int(os.getenv("DASHBOARD_TOKEN_MAX_AGE", str(14 * 24 * 3600)))
# Comma-separated origins for browser clients (GitHub Pages + local Vite). Tighten for production.
_cors_raw = os.getenv(
    "DASHBOARD_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:5175,"
    "http://127.0.0.1:5173,http://127.0.0.1:5174",
)
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in _cors_raw.split(",") if o.strip()]

BRIEF_CACHE_FILE = os.path.join(DOCUMENTS_DIR, "last_brief.txt")

_cached_serializer: Optional[URLSafeTimedSerializer] = None


def _serializer() -> Optional[URLSafeTimedSerializer]:
    global _cached_serializer
    if not SESSION_SECRET:
        return None
    if _cached_serializer is None:
        _cached_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="mason-dashboard-v1")
    return _cached_serializer


def _api_key_matches(provided: Optional[str]) -> bool:
    if not API_KEY or not provided:
        return False
    try:
        return secrets.compare_digest(provided.encode("utf-8"), API_KEY.encode("utf-8"))
    except ValueError:
        return False


def _password_matches(pw: str) -> bool:
    if not DASHBOARD_PASSWORD:
        return False
    try:
        return secrets.compare_digest(pw.encode("utf-8"), DASHBOARD_PASSWORD.encode("utf-8"))
    except ValueError:
        return False


def _bearer_token_valid(authorization: Optional[str]) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization[7:].strip()
    ser = _serializer()
    if not token or ser is None:
        return False
    try:
        data = ser.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return data.get("sub") == "mason"
    except (BadSignature, SignatureExpired, Exception):
        return False


def _oauth_state_serializer() -> Optional[URLSafeTimedSerializer]:
    if not SESSION_SECRET:
        return None
    return URLSafeTimedSerializer(SESSION_SECRET, salt="mason-google-oauth-state-v1")


def _oauth_redirect_uri() -> str:
    """Callback URL Google redirects to — must match one URI in Google Cloud for this OAuth client."""
    explicit = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    if explicit:
        return explicit
    base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if not base:
        base = "http://127.0.0.1:8000"
    return f"{base}/auth/google/callback"


def _google_flow():
    from google_auth_oauthlib.flow import Flow

    p = Path(CREDS_PATH)
    if not p.is_file():
        return None
    return Flow.from_client_secrets_file(
        str(p),
        scopes=GOOGLE_SCOPES,
        redirect_uri=_oauth_redirect_uri(),
    )


def _google_success_redirect_url() -> str:
    explicit = os.getenv("DASHBOARD_GOOGLE_SUCCESS_REDIRECT", "").strip().rstrip("/")
    if explicit:
        return explicit if "?" in explicit else explicit + "?google_connected=1"
    if ALLOWED_ORIGINS:
        return ALLOWED_ORIGINS[0].rstrip("/") + "/?google_connected=1"
    return "http://localhost:5173/?google_connected=1"


def _token_path_write() -> str:
    return TOKEN_PATH if isinstance(TOKEN_PATH, str) else str(TOKEN_PATH)


# Google Calendar default color IDs → hex (approximate)
GCAL_COLOR_HEX = {
    "1": "#a4bdfc",
    "2": "#7ae7bf",
    "3": "#dbadff",
    "4": "#ff887c",
    "5": "#fbd75b",
    "6": "#ffb878",
    "7": "#46d6db",
    "8": "#e1e1e1",
    "9": "#5484ed",
    "10": "#51b749",
    "11": "#dc2127",
}

app = FastAPI(title="Mason Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=[
        "*",
        "Authorization",
        "X-API-Key",
        "Content-Type",
        # Browsers send this on preflight when the dashboard adds ngrok's skip-interstitial header.
        "ngrok-skip-browser-warning",
    ],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    d = exc.detail
    if isinstance(d, dict) and "error" in d:
        return JSONResponse(status_code=exc.status_code, content=d)
    return JSONResponse(status_code=exc.status_code, content={"error": str(d)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errs = exc.errors()
    msg = errs[0].get("msg", "Invalid request") if errs else "Invalid request"
    return JSONResponse(status_code=422, content={"error": msg})


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)
    api_logger.info(f"{request.method} {request.url.path} | {response.status_code} | {elapsed_ms}ms")
    return response


async def verify_auth(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Accepts either:
    - Authorization: Bearer <signed token> from POST /auth/login, or
    - X-API-Key: <DASHBOARD_API_KEY> for scripts / monitoring (optional).
    """
    if _api_key_matches(x_api_key):
        return True
    if _bearer_token_valid(authorization):
        return True
    raise HTTPException(status_code=401, detail={"error": "Not authenticated"})


Auth = Depends(verify_auth)


# ── Pydantic models ───────────────────────────────────────────────────────


class HabitLogBody(BaseModel):
    habit: str
    completed: bool
    note: Optional[str] = None


class ChoreCompleteBody(BaseModel):
    chore_name: str
    note: Optional[str] = None


class GroceryAddBody(BaseModel):
    item: str


class GroceryRemoveBody(BaseModel):
    item: str


class TaskCompleteBody(BaseModel):
    title: str
    list_name: Optional[str] = None


class TaskAddBody(BaseModel):
    title: str
    list_name: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None


class ChatBody(BaseModel):
    message: str
    history: Optional[list[dict[str, Any]]] = None


class LoginBody(BaseModel):
    password: str = Field(..., min_length=1)


# ── Helpers (sync; run via run_in_threadpool) ─────────────────────────────


def _habit_emoji(name: str) -> str:
    return "💪" if name == "workout" else "💧" if name == "water" else "🧘"


def _habit_streak_count(habit: str) -> int:
    if not os.path.exists(HABIT_FILE):
        return 0
    with open(HABIT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    habit_lines = [l for l in lines if habit in l.lower()]
    today = date.today()
    streak = 0
    check_date = today
    while True:
        date_str = check_date.strftime("%Y-%m-%d")
        day_entries = [l for l in habit_lines if date_str in l]
        if day_entries and "✅" in day_entries[-1]:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def _habits_today_json() -> dict[str, Any]:
    today = date.today().strftime("%Y-%m-%d")
    out: list[dict[str, Any]] = []
    lines: list[str] = []
    if os.path.exists(HABIT_FILE):
        with open(HABIT_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

    for habit in HABITS:
        today_lines = [l for l in lines if today in l and habit in l.lower()]
        completed: bool | None = None
        note: str | None = None
        if today_lines:
            last = today_lines[-1]
            if "✅" in last:
                completed = True
            elif "❌" in last:
                completed = False
            m = re.search(r"—\s*(.+)$", last)
            if m and m.group(1).strip():
                note = m.group(1).strip()
        out.append(
            {
                "name": habit,
                "emoji": _habit_emoji(habit),
                "completed": completed,
                "note": note,
                "streak": _habit_streak_count(habit),
            }
        )
    return {"date": today, "habits": out}


def _habits_streak_json() -> dict[str, Any]:
    return {
        "streaks": {
            "workout": _habit_streak_count("workout"),
            "water": _habit_streak_count("water"),
            "stretching": _habit_streak_count("stretching"),
        }
    }


def _priority_from_notes(notes: str) -> tuple[str, str]:
    n = notes or ""
    if n.startswith("[HIGH]"):
        return "high", "🔴"
    if n.startswith("[MEDIUM]"):
        return "medium", "🟡"
    if n.startswith("[LOW]"):
        return "low", "⚪"
    return "medium", "🟡"


def _task_item_to_dict(t: dict, list_title: str) -> dict[str, Any]:
    due = t.get("due", "") or ""
    due_day = due[:10] if due else ""
    notes = t.get("notes", "") or ""
    pr, emoji = _priority_from_notes(notes)
    from agents.tasks_agent import is_overdue

    overdue = bool(due and is_overdue(due) and t.get("status") == "needsAction")
    return {
        "title": t.get("title", ""),
        "list": list_title,
        "due": due_day or "—",
        "priority": pr,
        "priority_emoji": emoji,
        "overdue": overdue,
    }


def _collect_tasks_due_today() -> list[dict]:
    from agents.tasks_agent import get_all_task_lists, get_tasks_service

    service = get_tasks_service()
    all_lists = get_all_task_lists(service)
    today_str = date.today().strftime("%Y-%m-%d")
    found: list[dict] = []
    for list_id, list_title in all_lists:
        result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
        for t in result.get("items", []):
            if t.get("due", "")[:10] == today_str and t.get("status") == "needsAction":
                found.append(_task_item_to_dict(t, list_title))
    return found


def _collect_tasks_overdue() -> list[dict]:
    from agents.tasks_agent import get_all_task_lists, get_tasks_service, is_overdue

    service = get_tasks_service()
    all_lists = get_all_task_lists(service)
    found: list[dict] = []
    for list_id, list_title in all_lists:
        result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
        for t in result.get("items", []):
            due = t.get("due", "")
            if due and is_overdue(due) and t.get("status") == "needsAction":
                d = _task_item_to_dict(t, list_title)
                d["overdue"] = True
                found.append(d)
    return found


def _collect_tasks_week() -> dict[str, list]:
    from agents.tasks_agent import get_all_task_lists, get_tasks_service

    service = get_tasks_service()
    all_lists = get_all_task_lists(service)
    today = date.today()
    week_end = today + timedelta(days=7)
    days: dict[str, list[dict]] = {}

    for list_id, list_title in all_lists:
        result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
        for t in result.get("items", []):
            due = t.get("due", "")
            if not due:
                continue
            due_date = due[:10]
            if today.strftime("%Y-%m-%d") <= due_date <= week_end.strftime("%Y-%m-%d"):
                if t.get("status") == "needsAction":
                    days.setdefault(due_date, []).append(_task_item_to_dict(t, list_title))
    return days


def _tasks_for_list(list_name: str) -> list[dict]:
    from agents.tasks_agent import find_list_by_name, get_tasks_service

    service = get_tasks_service()
    list_id, list_title = find_list_by_name(service, list_name)
    if not list_id:
        raise ValueError(f"List not found: {list_name}")
    result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
    return [_task_item_to_dict(t, list_title) for t in result.get("items", [])]


def _grocery_categories_json() -> dict[str, Any]:
    path = os.path.join(DOCUMENTS_DIR, LISTS["grocery"])
    categories: dict[str, list[str]] = {c: [] for c in GROCERY_CATEGORIES}
    uncategorized: list[str] = []
    if not os.path.exists(path):
        return {"categories": {k: v for k, v in categories.items() if v}, "total_items": 0}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            matched = False
            for cat in GROCERY_CATEGORIES:
                prefix = f"[{cat}]"
                if line.startswith(prefix):
                    categories[cat].append(line[len(prefix) :].strip())
                    matched = True
                    break
            if not matched:
                uncategorized.append(line)
    if uncategorized:
        categories["Other"] = uncategorized
    total = sum(len(v) for v in categories.values())
    return {"categories": categories, "total_items": total}


def _event_color_hex(event: dict) -> str:
    cid = event.get("colorId")
    if cid and str(cid) in GCAL_COLOR_HEX:
        return GCAL_COLOR_HEX[str(cid)]
    return "#4285f4"


def _calendar_day_events(target_date: date) -> dict[str, Any]:
    from agents.calendar_agent import get_all_calendar_ids, get_calendar_service

    service = get_calendar_service()
    cal_ids = get_all_calendar_ids(service)
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    start_local = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=tz)
    time_min = start_local.isoformat()
    time_max = end_local.isoformat()

    all_day: list[dict] = []
    timed: list[dict] = []

    for cal_id, cal_name in cal_ids:
        try:
            result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            for event in result.get("items", []):
                start = event["start"].get("dateTime", event["start"].get("date", ""))
                summary = event.get("summary", "(no title)")
                desc = event.get("description", "") or ""
                eid = event.get("id", "")
                if "T" not in start:
                    all_day.append(
                        {
                            "id": eid,
                            "title": summary,
                            "calendar": cal_name,
                            "color": _event_color_hex(event),
                        }
                    )
                else:
                    dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_s = event["end"].get("dateTime", "")
                    dt_end = dt_start
                    if end_s and "T" in end_s:
                        dt_end = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
                    timed.append(
                        {
                            "id": eid,
                            "title": summary,
                            "start": dt_start.isoformat(),
                            "end": dt_end.isoformat(),
                            "calendar": cal_name,
                            "color_hex": _event_color_hex(event),
                            "description": desc,
                        }
                    )
        except Exception:
            continue

    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "all_day_events": all_day,
        "events": timed,
    }


def _calendar_week_json() -> dict[str, Any]:
    out: dict[str, list[dict]] = {}
    today = date.today()
    for i in range(7):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        day_data = _calendar_day_events(d)
        merged: list[dict] = []
        for e in day_data["all_day_events"]:
            merged.append(
                {
                    "id": e.get("id", ""),
                    "title": e["title"],
                    "start": f"{key}T00:00:00",
                    "end": f"{key}T23:59:59",
                    "calendar": e["calendar"],
                    "color_hex": e.get("color", "#4285f4"),
                    "description": "",
                    "all_day": True,
                }
            )
        for e in day_data["events"]:
            merged.append({**e, "all_day": False})
        out[key] = merged
    return {"days": out}


def _parse_brief_text(raw: str) -> tuple[str, list[str], list[str]]:
    weather = ""
    m = re.search(r"WEATHER \(Houston, TX\):\s*\n(.*?)(?=\n\nTODAYS CALENDAR:|\n\n[A-Z][A-Z ]+:\s*\n)", raw, re.S)
    if m:
        weather = " ".join(
            line.strip() for line in m.group(1).strip().split("\n") if line.strip()
        )[:800]

    headlines: list[str] = []
    m = re.search(r"BREAKING / MAJOR NEWS:\s*\n(.*?)(?=\n\nWORLD NEWS:)", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-"):
                headlines.append(line.lstrip("- ").strip()[:500])
    headlines = headlines[:3]

    sports: list[str] = []
    m = re.search(r"SPORTS NEWS:\s*\n(?:Teams:.*\n)?(.*?)(?=\n\nTHIS WEEK AT A GLANCE:)", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-"):
                sports.append(line.lstrip("- ").strip()[:500])
    sports = sports[:8]

    if not weather:
        weather = raw[:400].replace("\n", " ").strip()

    if not headlines:
        headlines = ["—"]
    if not sports:
        sports = ["—"]

    return weather or "—", headlines, sports


def _parse_brief_file() -> dict[str, Any]:
    if not os.path.exists(BRIEF_CACHE_FILE):
        return {"error": "No brief available", "generated_at": None}

    mtime = os.path.getmtime(BRIEF_CACHE_FILE)
    generated_at = (
        datetime.utcfromtimestamp(mtime).replace(microsecond=0).isoformat() + "Z"
    )
    with open(BRIEF_CACHE_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    weather, headlines, sports = _parse_brief_text(raw)
    return {
        "generated_at": generated_at,
        "weather": weather,
        "headlines": headlines,
        "sports": sports,
    }


def _chore_status_for_today() -> list[dict]:
    from agents.chores_agent import (
        _chore_line_name,
        _parse_completion_log,
        setup_starter_chores,
        CHORES_FILE,
    )

    setup_starter_chores()
    today = date.today()
    today_tag = WEEKDAY_TAGS[today.weekday()]
    month = today.month

    with open(CHORES_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    daily = [l for l in lines if l.startswith("[DAILY]")]
    weekly_today = [l for l in lines if l.startswith(f"[{today_tag}]")]
    monthly = [l for l in lines if l.startswith("[MONTHLY]")] if today.day == 1 else []
    quarterly = (
        [l for l in lines if l.startswith("[QUARTERLY]")]
        if month in QUARTERLY_MONTHS and today.day <= 7
        else []
    )
    annual = (
        [l for l in lines if l.startswith("[ANNUALLY]")]
        if month in ANNUAL_MONTHS and today.day <= 7
        else []
    )

    candidates = daily + weekly_today + monthly + quarterly + annual
    log_rows = _parse_completion_log()
    last_done: dict[str, str] = {}
    for d, name, _ in log_rows:
        key = name.lower()
        if key not in last_done or d > last_done[key]:
            last_done[key] = d

    today_str = today.strftime("%Y-%m-%d")
    out = []
    for line in candidates:
        freq = line.split("]")[0].strip("[]") if "]" in line else ""
        name = _chore_line_name(line)
        key = name.lower()
        last = last_done.get(key)
        completed_today = last == today_str
        days_since = 0
        if last:
            try:
                ld = datetime.strptime(last, "%Y-%m-%d").date()
                days_since = (today - ld).days
            except Exception:
                days_since = 0
        out.append(
            {
                "name": name,
                "frequency": freq,
                "completed": completed_today,
                "last_done": last,
                "days_since": days_since,
            }
        )
    return out


def _chore_status_all_list() -> list[dict]:
    from agents.chores_agent import _chore_line_name, _parse_completion_log, setup_starter_chores, CHORES_FILE

    setup_starter_chores()
    today = date.today()
    with open(CHORES_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    log_rows = _parse_completion_log()
    last_done: dict[str, str] = {}
    for d, name, _ in log_rows:
        key = name.lower()
        if key not in last_done or d > last_done[key]:
            last_done[key] = d

    out = []
    for line in lines:
        freq = line.split("]")[0].strip("[]") if "]" in line else ""
        name = _chore_line_name(line)
        key = name.lower()
        last = last_done.get(key)
        completed_today = last == today.strftime("%Y-%m-%d")
        days_since = 0
        if last:
            try:
                ld = datetime.strptime(last, "%Y-%m-%d").date()
                days_since = (today - ld).days
            except Exception:
                days_since = 0
        out.append(
            {
                "name": name,
                "frequency": freq,
                "completed": completed_today,
                "last_done": last,
                "days_since": days_since,
            }
        )
    return out


def _regenerate_brief_sync() -> None:
    text = briefing_agent.get_daily_briefing()
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    with open(BRIEF_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(text)


# ── Routes ────────────────────────────────────────────────────────────────


@app.post("/auth/login")
async def auth_login(body: LoginBody):
    if not DASHBOARD_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail={"error": "DASHBOARD_PASSWORD not configured on server"},
        )
    ser = _serializer()
    if ser is None:
        raise HTTPException(
            status_code=503,
            detail={"error": "SESSION_SECRET not configured on server"},
        )
    if not _password_matches(body.password):
        raise HTTPException(status_code=401, detail={"error": "Invalid password"})
    token = ser.dumps({"sub": "mason"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_MAX_AGE_SECONDS,
    }


@app.post("/auth/logout")
async def auth_logout():
    """Stateless tokens: client discards the token; this endpoint is a no-op for API symmetry."""
    return {"success": True}


@app.get("/auth/me")
async def auth_me(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    if _api_key_matches(x_api_key):
        return {"authenticated": True, "via": "api_key"}
    if _bearer_token_valid(authorization):
        return {"authenticated": True, "via": "bearer"}
    return {"authenticated": False}


@app.get("/auth/google/config")
async def google_oauth_config():
    """Public: show Connect Google when credentials.json exists (same file Telegram uses)."""
    return {"web_oauth_ready": Path(CREDS_PATH).is_file()}


@app.post("/auth/google/start", dependencies=[Auth])
async def google_oauth_start():
    """Returns Google authorization URL (requires dashboard Bearer token)."""
    ser = _oauth_state_serializer()
    if ser is None:
        raise HTTPException(
            status_code=503,
            detail={"error": "SESSION_SECRET not configured"},
        )
    flow = _google_flow()
    if flow is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": (
                    "Missing credentials.json (same OAuth client as Telegram). "
                    "Add redirect URI in Google Cloud: " + _oauth_redirect_uri()
                ),
            },
        )
    state = ser.dumps({"sub": "mason"})
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
        include_granted_scopes="true",
    )
    return {"authorization_url": authorization_url}


@app.get("/auth/google/callback")
async def google_oauth_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: Optional[str] = Query(default=None),
):
    """OAuth redirect target (no Bearer). Writes token.json for Calendar + Tasks (same as Telegram)."""
    if error:
        raise HTTPException(status_code=400, detail={"error": error})
    if not code or not state:
        raise HTTPException(status_code=400, detail={"error": "Missing code or state"})
    ser = _oauth_state_serializer()
    if ser is None:
        raise HTTPException(status_code=503, detail={"error": "SESSION_SECRET not configured"})
    try:
        data = ser.loads(state, max_age=600)
        if data.get("sub") != "mason":
            raise ValueError("bad sub")
    except (BadSignature, SignatureExpired, ValueError, Exception):
        raise HTTPException(status_code=400, detail={"error": "Invalid or expired state"})
    flow = _google_flow()
    if flow is None:
        raise HTTPException(status_code=503, detail={"error": "Google OAuth not configured"})
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        api_logger.exception("google oauth fetch_token failed")
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    creds = flow.credentials
    with open(_token_path_write(), "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    api_logger.info("Google OAuth token stored (Connect Google)")
    return RedirectResponse(url=_google_success_redirect_url())


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}


@app.get("/habits/today", dependencies=[Auth])
async def habits_today():
    try:
        return await run_in_threadpool(_habits_today_json)
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/habits/streak", dependencies=[Auth])
async def habits_streak():
    try:
        return await run_in_threadpool(_habits_streak_json)
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/habits/log", dependencies=[Auth])
async def habits_log(body: HabitLogBody):
    try:
        msg = await run_in_threadpool(habits_agent.habit_log, body.habit, body.completed, body.note)
        return {"success": True, "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/chores/today", dependencies=[Auth])
async def chores_today():
    try:
        chores = await run_in_threadpool(_chore_status_for_today)
        return {"chores": chores}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/chores/status", dependencies=[Auth])
async def chores_status():
    try:
        chores = await run_in_threadpool(_chore_status_all_list)
        return {"chores": chores}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/chores/complete", dependencies=[Auth])
async def chores_complete(body: ChoreCompleteBody):
    try:
        msg = await run_in_threadpool(chores_agent.chore_complete, body.chore_name, body.note)
        ok = not str(msg).lower().startswith("could not")
        return {"success": ok, "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/grocery", dependencies=[Auth])
async def grocery():
    try:
        return await run_in_threadpool(_grocery_categories_json)
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/grocery/add", dependencies=[Auth])
async def grocery_add(body: GroceryAddBody):
    try:
        msg = await run_in_threadpool(lists_agent.list_add, "grocery", body.item)
        ok = str(msg).startswith("✅")
        cat = "Pantry"
        if "[" in msg and "]" in msg:
            m = re.search(r"\[([^\]]+)\]", msg)
            if m:
                cat = m.group(1)
        return {"success": ok, "category": cat, "item": body.item.strip(), "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/grocery/remove", dependencies=[Auth])
async def grocery_remove(body: GroceryRemoveBody):
    try:
        msg = await run_in_threadpool(lists_agent.list_remove, "grocery", body.item)
        ok = str(msg).startswith("✅")
        return {"success": ok, "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/tasks/today", dependencies=[Auth])
async def tasks_today():
    try:
        tasks = await run_in_threadpool(_collect_tasks_due_today)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/tasks/overdue", dependencies=[Auth])
async def tasks_overdue():
    try:
        tasks = await run_in_threadpool(_collect_tasks_overdue)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/tasks/week", dependencies=[Auth])
async def tasks_week():
    try:
        days = await run_in_threadpool(_collect_tasks_week)
        return {"days": days}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/tasks/list/{list_name}", dependencies=[Auth])
async def tasks_list_one(list_name: str):
    try:
        name = unquote(list_name)
        tasks = await run_in_threadpool(_tasks_for_list, name)
        return {"tasks": tasks}
    except ValueError as e:
        raise HTTPException(404, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/tasks/complete", dependencies=[Auth])
async def tasks_complete(body: TaskCompleteBody):
    try:
        msg = await run_in_threadpool(tasks_agent.tasks_complete, body.title, body.list_name)
        ok = str(msg).startswith("✅")
        return {"success": ok, "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/tasks/add", dependencies=[Auth])
async def tasks_add(body: TaskAddBody):
    try:
        msg = await run_in_threadpool(
            tasks_agent.tasks_add,
            body.title,
            body.list_name,
            None,
            body.due_date,
            body.priority,
        )
        ok = str(msg).startswith("✅")
        return {"success": ok, "message": msg}
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/calendar/today", dependencies=[Auth])
async def calendar_today():
    try:
        return await run_in_threadpool(_calendar_day_events, date.today())
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/calendar/week", dependencies=[Auth])
async def calendar_week():
    try:
        return await run_in_threadpool(_calendar_week_json)
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/calendar/tomorrow", dependencies=[Auth])
async def calendar_tomorrow():
    try:
        return await run_in_threadpool(_calendar_day_events, date.today() + timedelta(days=1))
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.get("/brief", dependencies=[Auth])
async def brief_get():
    try:
        data = await run_in_threadpool(_parse_brief_file)
        if data.get("error"):
            return data
        return {
            "generated_at": data["generated_at"],
            "weather": data["weather"],
            "headlines": data["headlines"],
            "sports": data["sports"],
        }
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})


@app.post("/brief/regenerate", dependencies=[Auth])
async def brief_regenerate(background_tasks: BackgroundTasks):
    background_tasks.add_task(_regenerate_brief_sync)
    return {"status": "generating", "message": "Brief will be ready shortly"}


@app.post("/chat", dependencies=[Auth])
async def chat_endpoint(body: ChatBody):
    messages: list[dict[str, Any]] = []
    if body.history:
        messages.extend(body.history)
    messages.append({"role": "user", "content": body.message})

    try:
        response_text = await asyncio.wait_for(
            asyncio.to_thread(run_agent_conversational, messages),
            timeout=60.0,
        )
        return {
            "response": response_text or "",
            "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }
    except asyncio.TimeoutError:
        raise HTTPException(504, detail={"error": "Agent timed out after 60 seconds"})
    except Exception as e:
        raise HTTPException(500, detail={"error": str(e)})
