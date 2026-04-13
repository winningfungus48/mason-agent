"""
schedulers/inbox_review_scheduler.py
-------------------------------------
Run via cron on the DigitalOcean server (America/Chicago), e.g. Saturday morning.
If Main List has pending items, sends a nudge to process the inbox.
Stays silent if the inbox is empty.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date
from telegram import Bot
from agents.tasks_agent import get_tasks_service, get_all_task_lists, find_list_by_name

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


async def send_inbox_nudge():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return

    try:
        service  = get_tasks_service()
        inbox_id, inbox_display = find_list_by_name(service, "main")
        if not inbox_id:
            all_lists = get_all_task_lists(service)
            if not all_lists:
                return
            inbox_id, inbox_display = all_lists[0]

        result = service.tasks().list(
            tasklist=inbox_id, maxResults=100, showCompleted=False
        ).execute()
        items = [t for t in result.get('items', []) if t.get('status') == 'needsAction']

        if not items:
            print("Inbox review: Main List is empty. No nudge sent.")
            return

        message = (
            f"📥 Weekly Inbox Review\n\n"
            f"You have {len(items)} item{'s' if len(items) != 1 else ''} in your Main List.\n"
            f"Say 'process my inbox' to sort them into your life-area lists."
        )

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Inbox nudge sent — {len(items)} items in Main List.")

    except Exception as e:
        print(f"Inbox review error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(send_inbox_nudge())
