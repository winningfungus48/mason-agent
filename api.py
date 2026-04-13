"""
FastAPI dashboard API for Mason's agent.
Imports existing agents — no duplicated business logic.
Run: uvicorn api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote

import zoneinfo
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

from agent import run_agent_conversational
from agents import briefing_agent, chores_agent, habits_agent, lists_agent, tasks_agent
from core.config import (
    DOCUMENTS_DIR,
    GROCERY_CATEGORIES,
    HABITS,
    HABIT_FILE,
    LISTS,
    QUARTERLY_MONTHS,
    ANNUAL_MONTHS,
    TIMEZONE,
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
BRIEF_CACHE_FILE = os.path.join(DOCUMENTS_DIR, "last_brief.txt")

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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    if not API_KEY:
        api_logger.warning("DASHBOARD_API_KEY not set — refusing authenticated routes")
        raise HTTPException(status_code=503, detail={"error": "API key not configured on server"})
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail={"error": "Invalid or missing API key"})
    return True


Auth = Depends(verify_api_key)


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
