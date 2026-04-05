"""
chore_scheduler.py
------------------
Run this via Windows Task Scheduler every morning.
On Saturday and Sunday it sends Mason his chores for the day via Telegram.
On the 1st of each month it also sends monthly maintenance reminders.
On the 1st of Jan/Apr/Jul/Oct it sends quarterly reminders.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import date
from telegram import Bot
from agent import get_todays_chores, get_maintenance_due

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Days to send chore reminders (5=Saturday, 6=Sunday)
CHORE_DAYS = [5, 6]
QUARTERLY_MONTHS = [1, 4, 7, 10]

async def send_chore_reminder():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return

    today = date.today()
    weekday = today.weekday()
    month = today.month
    messages = []

    # Send chore reminder on Saturday and Sunday
    if weekday in CHORE_DAYS:
        chores = get_todays_chores()
        messages.append(chores)

    # Send monthly maintenance reminder on 1st of month
    if today.day == 1:
        monthly = get_maintenance_due("monthly")
        messages.append(f"🗓 Monthly maintenance reminder:\n{monthly}")

    # Send quarterly maintenance reminder
    if month in QUARTERLY_MONTHS and today.day == 1:
        quarterly = get_maintenance_due("quarterly")
        messages.append(f"🔧 Quarterly maintenance reminder:\n{quarterly}")

    # Send annual reminder in January
    if month == 1 and today.day == 1:
        annual = get_maintenance_due("annually")
        messages.append(f"📆 Annual maintenance reminder:\n{annual}")

    if not messages:
        print(f"No chore reminders to send today ({today.strftime('%A')}).")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for msg in messages:
        if len(msg) <= 4096:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        else:
            chunks = [msg[i:i+4096] for i in range(0, len(msg), 4096)]
            for chunk in chunks:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)

    print(f"Chore reminder sent for {today.strftime('%A, %B %d, %Y')}")

if __name__ == "__main__":
    asyncio.run(send_chore_reminder())
