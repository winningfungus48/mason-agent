"""
agents/chores_agent.py
----------------------
Chore and home maintenance functions for Mason's Personal Agent.
"""

import os
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
