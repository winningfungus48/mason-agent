"""
meal_scheduler.py
-----------------
Run via Windows Task Scheduler every Friday evening.
Generates Mason's weekly meal plan and sends it to Telegram.
Asks Mason if he wants to update his grocery list.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from meal_agent import generate_meal_plan

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_meal_plan():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return

    print("Generating weekly meal plan...")
    result = generate_meal_plan()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Send the meal plan
    plan_message = result["plan"]
    if len(plan_message) <= 4096:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=plan_message)
    else:
        chunks = [plan_message[i:i+4096] for i in range(0, len(plan_message), 4096)]
        for chunk in chunks:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)

    # Ask about grocery list
    grocery_count = len(result["grocery_items"])
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=f"Your meal plan is ready! 🎉\n\nI found {grocery_count} grocery items needed for this plan.\n\nReply 'yes add groceries' to add them to your grocery list, or 'show groceries' to see the list first."
    )

    print("Meal plan sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_meal_plan())
