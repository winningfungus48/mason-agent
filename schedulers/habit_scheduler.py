"""
habit_scheduler.py
-------------------
Run via Windows Task Scheduler twice daily:
- Morning (e.g. 8:00 AM) — asks if yesterday's habits were completed
- Evening (e.g. 8:00 PM) — asks if today's habits were completed

Pass argument 'morning' or 'evening' when running:
  python habit_scheduler.py morning
  python habit_scheduler.py evening
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import asyncio
from datetime import date, timedelta
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HABITS = [
    ("workout", "💪 Did you work out?"),
    ("water", "💧 Did you drink enough water?"),
    ("stretching", "🧘 Did you stretch / do mobility work?"),
]

async def send_checkin(period):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    if period == "morning":
        yesterday = (date.today() - timedelta(days=1)).strftime("%A")
        msg = f"☀️ Good morning Mason! Quick habit check-in for yesterday ({yesterday}):\n\n"
        for _, question in HABITS:
            msg += f"{question}\n"
        msg += "\nJust reply with what you did or didn't do — e.g. 'yes workout, no water, yes stretching'"

    elif period == "evening":
        today = date.today().strftime("%A")
        msg = f"🌙 Evening check-in Mason! How did today ({today}) go?\n\n"
        for _, question in HABITS:
            msg += f"{question}\n"
        msg += "\nJust reply naturally — e.g. 'worked out, skipped stretching, drank lots of water'"

    else:
        print(f"Unknown period: {period}. Use 'morning' or 'evening'.")
        return

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    print(f"Habit {period} check-in sent!")

if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "evening"
    asyncio.run(send_checkin(period))
