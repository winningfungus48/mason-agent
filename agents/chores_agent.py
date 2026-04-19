"""
agents/chores_agent.py
----------------------
Chore and home maintenance functions for Mason's Personal Agent.
"""

import os
import datetime
from datetime import date
from core.config import DOCUMENTS_DIR, WEEKDAY_TAGS, QUARTERLY_MONTHS, ANNUAL_MONTHS
from core.display import wrap_display

CHORES_FILE = os.path.join(DOCUMENTS_DIR, "chores.txt")


def setup_starter_chores():
    """Create chores.txt with starter list if it doesn't exist."""
    if not os.path.exists(CHORES_FILE):
        starter = """[DAILY] Make bed
[DAILY] Dishes / kitchen cleanup
[DAILY] Wipe down kitchen counters
[DAILY] Take out trash if full
[WEEKLY-SAT] Vacuum all rooms
[WEEKLY-SAT] Mop floors
[WEEKLY-SAT] Clean bathrooms
[WEEKLY-SUN] Do laundry
[WEEKLY-SUN] Change bed sheets
[WEEKLY-SUN] Wipe down appliances
[WEEKLY-SUN] Take out recycling
[MONTHLY] Deep clean bathroom grout
[MONTHLY] Clean microwave inside
[MONTHLY] Wipe baseboards
[MONTHLY] Clean ceiling fans
[QUARTERLY] Change AC filter
[QUARTERLY] Test smoke detectors
[QUARTERLY] Clean refrigerator coils
[QUARTERLY] Check water heater
[ANNUALLY] Deep clean oven
[ANNUALLY] Clean dryer vent
[ANNUALLY] Check fire extinguisher
[ANNUALLY] Inspect roof / gutters
[ANNUALLY] Flush water heater
"""
        with open(CHORES_FILE, "w", encoding="utf-8") as f:
            f.write(starter)
        return True
    return False


def get_todays_chores():
    try:
        print("  [TOOL] Getting today's chores")
        today = date.today()
        weekday = today.weekday()
        today_tag = WEEKDAY_TAGS[weekday]
        month = today.month

        setup_starter_chores()
        with open(CHORES_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        daily        = [l for l in lines if l.startswith("[DAILY]")]
        weekly_today = [l for l in lines if l.startswith(f"[{today_tag}]")]
        monthly      = [l for l in lines if l.startswith("[MONTHLY]")]  if today.day == 1 else []
        quarterly    = [l for l in lines if l.startswith("[QUARTERLY]")] if month in QUARTERLY_MONTHS and today.day <= 7 else []
        annual       = [l for l in lines if l.startswith("[ANNUALLY]")]  if month in ANNUAL_MONTHS and today.day <= 7 else []

        result = f"🏠 TODAY'S CHORES ({today.strftime('%A, %B %d')}):\n\n"
        if daily:
            result += "📌 DAILY:\n" + "\n".join(f"• {l.replace('[DAILY] ', '')}" for l in daily) + "\n\n"
        if weekly_today:
            result += f"📅 TODAY ({today.strftime('%A')}):\n" + "\n".join(f"• {l.split('] ', 1)[1]}" for l in weekly_today) + "\n\n"
        if monthly:
            result += "🗓 THIS MONTH:\n" + "\n".join(f"• {l.replace('[MONTHLY] ', '')}" for l in monthly) + "\n\n"
        if quarterly:
            result += "🔧 THIS QUARTER:\n" + "\n".join(f"• {l.replace('[QUARTERLY] ', '')}" for l in quarterly) + "\n\n"
        if annual:
            result += "📆 THIS YEAR:\n" + "\n".join(f"• {l.replace('[ANNUALLY] ', '')}" for l in annual) + "\n\n"
        if not any([daily, weekly_today, monthly, quarterly, annual]):
            result += "Nothing scheduled for today!"

        return wrap_display(result.strip())
    except Exception as e:
        return f"Error getting chores: {str(e)}"


def reschedule_chore(chore, new_frequency):
    try:
        print(f"  [TOOL] Rescheduling chore: {chore} → {new_frequency}")
        if not os.path.exists(CHORES_FILE):
            return "No chores list found."
        with open(CHORES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        updated = False
        new_lines = []
        for line in lines:
            if chore.lower() in line.lower():
                old_tag = line.strip().split("]")[0] + "]"
                new_lines.append(line.replace(old_tag, f"[{new_frequency.upper()}]"))
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            return f"Could not find chore matching '{chore}'."
        with open(CHORES_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return f"✅ Rescheduled '{chore}' to [{new_frequency.upper()}]"
    except Exception as e:
        return f"Error rescheduling chore: {str(e)}"


def get_maintenance_due(period):
    try:
        print(f"  [TOOL] Getting {period} maintenance tasks")
        setup_starter_chores()
        with open(CHORES_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        tag_map = {"monthly": "MONTHLY", "quarterly": "QUARTERLY", "annually": "ANNUALLY"}
        tag = tag_map.get(period.lower(), period.upper())
        items = [l for l in lines if l.startswith(f"[{tag}]")]
        if not items:
            return f"No {period} maintenance tasks found."

        content = f"🔧 {period.upper()} MAINTENANCE:\n" + "\n".join(
            f"• {l.split('] ', 1)[1]}" for l in items
        )
        return wrap_display(content)
    except Exception as e:
        return f"Error getting maintenance: {str(e)}"


# ── Completion log (used by Telegram tools + dashboard API) ─────────────
CHORE_LOG_FILE = os.path.join(DOCUMENTS_DIR, "chore_completions.txt")


def _chore_line_name(line: str) -> str:
    line = line.strip()
    if "] " in line:
        return line.split("] ", 1)[1].strip()
    return line


def _read_chore_lines():
    setup_starter_chores()
    with open(CHORES_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]


def _parse_completion_log():
    """Return list of (date_str, chore_display_name, note) newest last."""
    if not os.path.exists(CHORE_LOG_FILE):
        return []
    rows = []
    with open(CHORE_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) >= 2:
                d, name = parts[0], parts[1]
                note = parts[2] if len(parts) > 2 else ""
                rows.append((d, name, note))
    return rows


def append_chore_completion(display_name: str, note=None):
    """Append one line to chore_completions.txt (existing pipe format)."""
    today = date.today().strftime("%Y-%m-%d")
    note = note or ""
    entry = f"{today}|{display_name}|{note}\n"
    with open(CHORE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def chore_complete(chore_name_input, note=None):
    """Log a chore as completed today (fuzzy match against chores.txt lines)."""
    try:
        print(f"  [TOOL] chore_complete: {chore_name_input}")
        name_q = chore_name_input.strip().lower()
        if not name_q:
            return "No chore name provided."
        lines = _read_chore_lines()
        matched_display = None
        for line in lines:
            disp = _chore_line_name(line)
            if name_q in disp.lower() or disp.lower() in name_q:
                matched_display = disp
                break
        if not matched_display:
            return f"Could not find a chore matching '{chore_name_input}'."

        append_chore_completion(matched_display, note)
        return f"✅ Logged completion: {matched_display}"
    except Exception as e:
        return f"Error logging chore: {str(e)}"


def chore_history_view(chore=None, limit=20):
    try:
        rows = _parse_completion_log()
        if chore:
            c = chore.lower()
            rows = [r for r in rows if c in r[1].lower()]
        rows = rows[-limit:]
        if not rows:
            return "No chore completions logged yet."
        lines = [f"{d} — {n}" + (f" ({note})" if note else "") for d, n, note in rows]
        return wrap_display("📜 CHORE HISTORY:\n" + "\n".join(lines))
    except Exception as e:
        return f"Error: {str(e)}"


def chore_last_done(chore):
    try:
        rows = _parse_completion_log()
        c = chore.lower()
        best = None
        for d, n, _note in reversed(rows):
            if c in n.lower():
                best = (d, n)
                break
        if not best:
            return f"No completion log found for '{chore}'."
        return f"Last done: {best[1]} on {best[0]}"
    except Exception as e:
        return f"Error: {str(e)}"


def chore_status_all():
    """Full chore list with done/pending and days since last completion (from log)."""
    try:
        setup_starter_chores()
        lines = _read_chore_lines()
        log_rows = _parse_completion_log()
        last_by_name = {}
        for d, n, _ in log_rows:
            key = n.lower()
            if key not in last_by_name or d > last_by_name[key][0]:
                last_by_name[key] = (d, n)

        today = date.today()
        out = "📋 ALL CHORES:\n\n"
        for line in lines:
            disp = _chore_line_name(line)
            tag = line.split("]")[0] + "]" if line.startswith("[") else "[?]"
            key = disp.lower()
            done_info = last_by_name.get(key)
            if done_info:
                last_d = datetime.datetime.strptime(done_info[0], "%Y-%m-%d").date()
                days_ago = (today - last_d).days
                status = f"✅ last {done_info[0]} ({days_ago}d ago)"
            else:
                status = "⏳ no log yet"
            out += f"• {disp} {tag} — {status}\n"
        return wrap_display(out.strip())
    except Exception as e:
        return f"Error: {str(e)}"


def chore_add(chore_name_input, frequency):
    try:
        setup_starter_chores()
        freq = frequency.strip().upper()
        if not freq.startswith("["):
            freq = f"[{freq}]"
        new_line = f"{freq} {chore_name_input.strip()}\n"
        with open(CHORES_FILE, "a", encoding="utf-8") as f:
            f.write(new_line)
        return f"✅ Added chore: {new_line.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"


def chore_remove(chore_name_input):
    try:
        lines = _read_chore_lines()
        name_q = chore_name_input.strip().lower()
        new_lines = []
        removed = False
        for line in lines:
            disp = _chore_line_name(line)
            if name_q in disp.lower() and not removed:
                removed = True
                continue
            new_lines.append(line)
        if not removed:
            return f"No chore matching '{chore_name_input}'."
        with open(CHORES_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        return f"🗑️ Removed chore matching '{chore_name_input}'"
    except Exception as e:
        return f"Error: {str(e)}"
