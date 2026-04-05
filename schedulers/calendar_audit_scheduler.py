"""
calendar_audit_scheduler.py
----------------------------
Run via Windows Task Scheduler every 2 weeks.
Scans for uncategorized calendar events and sends Mason a Telegram message.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from telegram import Bot
from agent import calendar_audit_uncategorized

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_audit():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return

    print("Running calendar audit...")
    result = calendar_audit_uncategorized()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    if len(result) <= 4096:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=result)
    else:
        chunks = [result[i:i+4096] for i in range(0, len(result), 4096)]
        for chunk in chunks:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)

    print("Calendar audit sent!")

if __name__ == "__main__":
    asyncio.run(send_audit())
