"""
core/telegram_utils.py
----------------------
Shared Telegram messaging utilities.
Used by agent.py and all scheduler scripts.
Handles the 4096-character message limit automatically.
"""

import os
import asyncio
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


async def send_message_async(text: str, chat_id: str = None):
    """Send a message to Telegram, splitting if over 4096 chars."""
    token = TELEGRAM_BOT_TOKEN
    cid   = chat_id or TELEGRAM_CHAT_ID

    if not token or not cid:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return

    bot = Bot(token=token)
    if len(text) <= 4096:
        await bot.send_message(chat_id=cid, text=text)
    else:
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
        for chunk in chunks:
            await bot.send_message(chat_id=cid, text=chunk)


def send_message(text: str, chat_id: str = None):
    """Synchronous wrapper around send_message_async."""
    asyncio.run(send_message_async(text, chat_id))
