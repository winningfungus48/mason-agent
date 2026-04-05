"""
agents/habits_agent.py
----------------------
Habit tracking functions for Mason's Personal Agent.
Tracks workout, water, and stretching habits.
"""

import os
import re
import datetime
from datetime import date
from core.config import HABITS, HABIT_FILE
from core.display import wrap_display


def habit_log(habit, completed, note=None):
    try:
        print(f"  [TOOL] Logging habit: {habit} = {completed}")
        habit = habit.lower().strip()
        matched = next((h for h in HABITS if habit in h or h in habit), None)
        if not matched:
            return f"Unknown habit '{habit}'. Available habits: {', '.join(HABITS)}"

        today = date.today().strftime("%Y-%m-%d")
        status = "✅" if completed else "❌"
        note_str = f" — {note}" if note else ""
        entry = f"[{today}] {matched}: {status}{note_str}\n"

        with open(HABIT_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        emoji = "💪" if matched == "workout" else "💧" if matched == "water" else "🧘"
        result = "Nice work!" if completed else "No worries, get it tomorrow!"
        return f"{emoji} Logged {matched}: {status} {result}"
    except Exception as e:
        return f"Error logging habit: {str(e)}"


def habit_view(habit=None, period=None):
    try:
        print("  [TOOL] Viewing habits")
        if not os.path.exists(HABIT_FILE):
            return "No habit data yet. Start logging with 'I worked out today' or 'logged water'."

        with open(HABIT_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if not lines:
            return "No habit entries yet."

        if habit and habit.lower() != "all":
            lines = [l for l in lines if habit.lower() in l.lower()]

        today = date.today()
        if period == "today":
            today_str = today.strftime("%Y-%m-%d")
            lines = [l for l in lines if today_str in l]
        elif period in ["this_week", "last_7_days"]:
            week_ago = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            lines = [l for l in lines if l[1:11] >= week_ago]

        if not lines:
            return "No habit entries found for the selected filters."

        def reformat_line(line):
            match = re.match(r'\[(\d{4})-(\d{2})-(\d{2})\](.*)', line)
            if match:
                y, m, d_str, rest = match.groups()
                dt = datetime.date(int(y), int(m), int(d_str))
                label = f"{dt.strftime('%a')}, {int(m)}.{int(d_str)}.{y[2:]}"
                return f"{label} -{rest}"
            return line

        formatted = [reformat_line(l) for l in lines[-30:]]
        content = "📊 HABIT LOG:\n" + "\n".join(f"• {l}" for l in formatted)
        return wrap_display(content)
    except Exception as e:
        return f"Error viewing habits: {str(e)}"


def habit_streak():
    try:
        print("  [TOOL] Getting habit streaks")
        if not os.path.exists(HABIT_FILE):
            return "No habit data yet. Start tracking to see your streaks!"

        with open(HABIT_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        today = date.today()
        output = "🔥 HABIT STREAKS & THIS WEEK:\n\n"

        for habit in HABITS:
            emoji = "💪" if habit == "workout" else "💧" if habit == "water" else "🧘"
            habit_lines = [l for l in lines if habit in l.lower()]

            week_start   = today - datetime.timedelta(days=today.weekday())
            week_entries = [l for l in habit_lines if l[1:11] >= week_start.strftime("%Y-%m-%d")]
            completed_this_week = sum(1 for l in week_entries if "✅" in l)
            total_this_week     = len(week_entries)

            streak = 0
            check_date = today
            while True:
                date_str   = check_date.strftime("%Y-%m-%d")
                day_entries = [l for l in habit_lines if date_str in l]
                if day_entries and "✅" in day_entries[-1]:
                    streak += 1
                    check_date -= datetime.timedelta(days=1)
                else:
                    break

            output += f"{emoji} {habit.capitalize()}:\n"
            output += f"   Streak: {streak} day{'s' if streak != 1 else ''} 🔥\n"
            output += f"   This week: {completed_this_week}/{total_this_week if total_this_week else '?'} days\n\n"

        return wrap_display(output.strip())
    except Exception as e:
        return f"Error getting streaks: {str(e)}"
