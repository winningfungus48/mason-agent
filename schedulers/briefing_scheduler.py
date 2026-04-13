"""
briefing_scheduler.py
---------------------
Run via cron on the DigitalOcean server (America/Chicago), e.g. every morning ~6:00 AM.
It generates Mason's daily briefing and sends it to Telegram automatically.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from telegram import Bot
from agent import run_agent_conversational

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_morning_briefing():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set.")
        return

    print("Generating morning briefing...")

    # Run the agent with a briefing request
    history = [{"role": "user", "content": "Give me my daily briefing"}]
    briefing = run_agent_conversational(history)

    # Send via Telegram — split if over 4096 chars
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    if len(briefing) <= 4096:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=briefing)
    else:
        chunks = [briefing[i:i+4096] for i in range(0, len(briefing), 4096)]
        for chunk in chunks:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)

    print("Morning briefing sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_morning_briefing())
