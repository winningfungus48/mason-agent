"""
tasks_scheduler.py
------------------
Run via Windows Task Scheduler daily (suggested: 8:30 AM, after morning briefing).
Checks for overdue tasks and tasks due today. Sends a Telegram nudge if anything needs attention.
Skips silently if everything is clear.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from telegram import Bot
import tasks_agent

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_tasks_nudge():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    messages = []

    # Check overdue
    overdue = tasks_agent.tasks_overdue()
    if "[DISPLAY_RAW]" in overdue:
        content = overdue.split("[DISPLAY_RAW]")[1].split("[/DISPLAY_RAW]")[0].strip()
        messages.append(content)

    # Check due today
    due_today = tasks_agent.tasks_due_today()
    if "[DISPLAY_RAW]" in due_today:
        content = due_today.split("[DISPLAY_RAW]")[1].split("[/DISPLAY_RAW]")[0].strip()
        # Only add if not already covered by overdue
        if "TASKS DUE TODAY" in content and "No tasks due today" not in content:
            messages.append(content)

    if not messages:
        print("Tasks scheduler: nothing due or overdue. No message sent.")
        return

    full_message = "\n\n".join(messages)
    if len(full_message) <= 4096:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=full_message)
    else:
        chunks = [full_message[i:i+4096] for i in range(0, len(full_message), 4096)]
        for chunk in chunks:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)

    print("Tasks nudge sent.")

if __name__ == "__main__":
    asyncio.run(send_tasks_nudge())
