"""
JSON-backed chore schedule (documents/chores.json) + completion merge from chore_completions.txt.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Any, Iterator, Optional

from agents.chores_agent import _parse_completion_log
from core.config import DOCUMENTS_DIR

CHORES_JSON = os.path.join(DOCUMENTS_DIR, "chores.json")

DAY_KEYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKLY_DAY_ORDER = ("sunday", "monday", "tuesday", "wednesday", "thursday")


def load_chores_json() -> dict[str, Any]:
    if not os.path.isfile(CHORES_JSON):
        raise FileNotFoundError(f"Missing schedule file: {CHORES_JSON}")
    with open(CHORES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def day_key(d: date) -> str:
    return DAY_KEYS[d.weekday()]


def first_sunday_of_month(year: int, month: int) -> date:
    d = date(year, month, 1)
    days_ahead = (6 - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def is_first_sunday(d: date) -> bool:
    return d == first_sunday_of_month(d.year, d.month)


def quarter_start_for_date(d: date) -> date:
    m = d.month
    if m <= 3:
        return date(d.year, 1, 1)
    if m <= 6:
        return date(d.year, 4, 1)
    if m <= 9:
        return date(d.year, 7, 1)
    return date(d.year, 10, 1)


def _same_iso_week(a: date, b: date) -> bool:
    return a.isocalendar()[:2] == b.isocalendar()[:2]


def _same_calendar_month(a: date, ref: date) -> bool:
    return a.year == ref.year and a.month == ref.month


def _same_calendar_quarter(a: date, ref: date) -> bool:
    return a.year == ref.year and (a.month - 1) // 3 == (ref.month - 1) // 3


def chore_name_matches(chore: dict[str, Any], log_name: str) -> bool:
    cn = chore["name"].strip().lower()
    ln = log_name.strip().lower()
    if cn == ln:
        return True
    if cn in ln or ln in cn:
        return True
    cid = chore.get("id", "")
    if cid and cid.lower() in ln:
        return True
    return False


def _matching_log_dates(chore: dict[str, Any], log_rows: list[tuple[str, str, str]]) -> list[date]:
    out: list[date] = []
    for d_str, n, _ in log_rows:
        if not chore_name_matches(chore, n):
            continue
        try:
            out.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            continue
    return out


def get_completion_status(
    chore: dict[str, Any],
    frequency: str,
    today: date,
    log_rows: list[tuple[str, str, str]],
) -> dict[str, Any]:
    dates = _matching_log_dates(chore, log_rows)
    last_date = max(dates) if dates else None
    last_done = last_date.strftime("%Y-%m-%d") if last_date else None

    completed = False
    if frequency == "weekly":
        for d in dates:
            if _same_iso_week(d, today):
                completed = True
                break
    elif frequency == "monthly":
        for d in dates:
            if _same_calendar_month(d, today):
                completed = True
                break
    elif frequency == "quarterly":
        for d in dates:
            if _same_calendar_quarter(d, today):
                completed = True
                break

    days_since: Optional[int] = None
    if last_date is not None:
        days_since = (today - last_date).days

    q_start = quarter_start_for_date(today)
    overdue = False
    if frequency == "quarterly":
        overdue = last_date is None or last_date < q_start

    return {
        "completed": completed,
        "last_done": last_done,
        "days_since": days_since,
        "overdue": overdue,
    }


def _enrich(
    chore: dict[str, Any],
    frequency: str,
    today: date,
    log_rows: list[tuple[str, str, str]],
    *,
    include_overdue: bool = False,
    due_label: Optional[str] = None,
    schedule: Optional[str] = None,
) -> dict[str, Any]:
    st = get_completion_status(chore, frequency, today, log_rows)
    row: dict[str, Any] = {
        "id": chore["id"],
        "name": chore["name"],
        "category": chore["category"],
        "emoji": chore["emoji"],
        "completed": st["completed"],
        "last_done": st["last_done"],
        "days_since": st["days_since"],
    }
    if schedule:
        row["schedule"] = schedule
    if due_label:
        row["due_label"] = due_label
    if include_overdue:
        row["overdue"] = st["overdue"]
    return row


def iter_all_chores(data: dict[str, Any]) -> Iterator[tuple[dict[str, Any], str]]:
    for _dk, block in data.get("weekly", {}).items():
        for c in block.get("chores", []):
            yield c, "weekly"
    for c in data.get("monthly", {}).get("chores", []):
        yield c, "monthly"
    for c in data.get("quarterly", {}).get("chores", []):
        yield c, "quarterly"


def find_chore_by_id_or_name(
    data: dict[str, Any],
    chore_id: Optional[str],
    chore_name: Optional[str],
) -> Optional[dict[str, Any]]:
    cid = (chore_id or "").strip()
    cname = (chore_name or "").strip()
    if cid:
        for c, _freq in iter_all_chores(data):
            if c.get("id") == cid:
                return c
    if cname:
        cn = cname.lower()
        for c, _freq in iter_all_chores(data):
            if c["name"].strip().lower() == cn:
                return c
        for c, _freq in iter_all_chores(data):
            disp = c["name"].strip().lower()
            if cn in disp or disp in cn:
                return c
    return None


def build_chores_today(for_date: Optional[date] = None) -> dict[str, Any]:
    today = for_date or date.today()
    dk = day_key(today)
    data = load_chores_json()
    log_rows = _parse_completion_log()
    weekly = data.get("weekly", {})

    message: Optional[str] = None
    chores_out: list[dict[str, Any]] = []

    if dk in ("friday", "saturday"):
        message = "No chores scheduled today — enjoy your day off 🎉"
    else:
        block = weekly.get(dk) or {}
        for c in block.get("chores", []):
            chores_out.append(_enrich(c, "weekly", today, log_rows, schedule="weekly"))

    if is_first_sunday(today):
        for c in data.get("monthly", {}).get("chores", []):
            chores_out.append(_enrich(c, "monthly", today, log_rows, schedule="monthly"))

    total = len(chores_out)
    completed_n = sum(1 for x in chores_out if x["completed"])
    summary = {"total": total, "completed": completed_n, "pending": total - completed_n}

    day_label = ""
    day_emoji = ""
    if dk in ("friday", "saturday"):
        day_label = ""
        day_emoji = ""
    elif dk in weekly:
        day_label = weekly[dk].get("label", "")
        day_emoji = weekly[dk].get("emoji", "")

    return {
        "date": today.strftime("%Y-%m-%d"),
        "day": dk,
        "day_label": day_label,
        "day_emoji": day_emoji,
        "chores": chores_out,
        "summary": summary,
        "message": message,
    }


def build_chores_week(for_date: Optional[date] = None) -> dict[str, Any]:
    today = for_date or date.today()
    data = load_chores_json()
    log_rows = _parse_completion_log()
    weekly = data.get("weekly", {})
    days_out: dict[str, Any] = {}
    for day_key in WEEKLY_DAY_ORDER:
        block = weekly.get(day_key, {})
        chores = [_enrich(c, "weekly", today, log_rows) for c in block.get("chores", [])]
        sm = {
            "total": len(chores),
            "completed": sum(1 for x in chores if x["completed"]),
            "pending": sum(1 for x in chores if not x["completed"]),
        }
        days_out[day_key] = {
            "label": block.get("label", ""),
            "emoji": block.get("emoji", ""),
            "chores": chores,
            "summary": sm,
            "all_done": sm["total"] > 0 and sm["pending"] == 0,
        }
    return {"days": days_out}


def build_chores_monthly(for_date: Optional[date] = None) -> dict[str, Any]:
    today = for_date or date.today()
    data = load_chores_json()
    log_rows = _parse_completion_log()
    block = data.get("monthly", {})
    chores = [
        _enrich(
            c,
            "monthly",
            today,
            log_rows,
            due_label="Due by first Sunday",
        )
        for c in block.get("chores", [])
    ]
    total = len(chores)
    sm = {
        "total": total,
        "completed": sum(1 for x in chores if x["completed"]),
        "pending": sum(1 for x in chores if not x["completed"]),
    }
    return {
        "label": block.get("label", ""),
        "emoji": block.get("emoji", ""),
        "chores": chores,
        "summary": sm,
    }


def build_chores_quarterly(for_date: Optional[date] = None) -> dict[str, Any]:
    today = for_date or date.today()
    data = load_chores_json()
    log_rows = _parse_completion_log()
    block = data.get("quarterly", {})
    qs = quarter_start_for_date(today)
    quarter_label = f"Q{(today.month - 1) // 3 + 1} · since {qs.strftime('%b %d, %Y')}"
    chores = [
        _enrich(c, "quarterly", today, log_rows, include_overdue=True) for c in block.get("chores", [])
    ]
    total = len(chores)
    sm = {
        "total": total,
        "completed": sum(1 for x in chores if x["completed"]),
        "pending": sum(1 for x in chores if not x["completed"]),
    }
    return {
        "label": block.get("label", ""),
        "emoji": block.get("emoji", ""),
        "quarter_start": qs.strftime("%Y-%m-%d"),
        "quarter_label": quarter_label,
        "chores": chores,
        "summary": sm,
    }


def build_chores_all(for_date: Optional[date] = None) -> dict[str, Any]:
    today = for_date or date.today()
    return {
        "date": today.strftime("%Y-%m-%d"),
        "today": build_chores_today(today),
        "week": build_chores_week(today),
        "monthly": build_chores_monthly(today),
        "quarterly": build_chores_quarterly(today),
    }


def complete_chore_from_schedule(
    chore_id: Optional[str],
    chore_name: Optional[str],
    note: Optional[str],
) -> tuple[bool, str]:
    try:
        data = load_chores_json()
    except FileNotFoundError as e:
        return False, str(e)
    chore = find_chore_by_id_or_name(data, chore_id, chore_name)
    if not chore:
        q = (chore_name or chore_id or "").strip() or "unknown"
        return False, f"Could not find a chore matching '{q}'."

    from agents.chores_agent import append_chore_completion

    append_chore_completion(chore["name"], note)
    return True, f"✅ Logged: {chore['name']}"
