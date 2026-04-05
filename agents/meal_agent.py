"""
meal_agent.py
-------------
Dedicated meal planning agent (Agent 2).
Called by Agent 1 when Mason requests a meal plan.
Reads meal_preferences.txt and generates a full weekly plan
with dinners and lunches, then returns the plan as a string.
"""

import os
import anthropic
from datetime import date

client = anthropic.Anthropic()

from core.config import DOCUMENTS_DIR as DOCUMENTS_PATH

def read_preferences():
    """Read Mason's meal preferences file."""
    filepath = os.path.join(DOCUMENTS_PATH, "meal_preferences.txt")
    if not os.path.exists(filepath):
        return "No preferences file found. Generate a balanced varied meal plan."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def save_meal_plan(plan):
    """Save the generated meal plan to meal_plan.txt."""
    filepath = os.path.join(DOCUMENTS_PATH, "meal_plan.txt")
    today = date.today().strftime("%Y-%m-%d")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"MEAL PLAN GENERATED: {today}\n\n")
        f.write(plan)
    return filepath

def update_grocery_list(grocery_items):
    """Append grocery items from the meal plan to grocery.txt."""
    filepath = os.path.join(DOCUMENTS_PATH, "grocery.txt")
    with open(filepath, "a", encoding="utf-8") as f:
        for item in grocery_items:
            f.write(item.strip() + "\n")

def generate_meal_plan():
    """
    Main function — generates a weekly meal plan using Claude.
    Returns a dict with:
      - plan: full formatted meal plan string
      - grocery_items: list of grocery items needed
    """
    print("[Meal Agent] Reading preferences...")
    preferences = read_preferences()
    today = date.today().strftime("%A, %B %d, %Y")

    prompt = f"""You are a personal meal planning assistant for Mason in Houston, TX.
Today is {today}.

Here are Mason's meal preferences:
{preferences}

Generate a complete weekly meal plan for the upcoming week (Monday through Sunday).
Include:
- 7 dinners (one per night)
- 5 weekday lunches (Monday–Friday)

Format the plan exactly like this:

🍽️ WEEKLY MEAL PLAN
Week of [start date] – [end date]

DINNERS:
Monday: [meal name] — [brief 1 sentence description]
Tuesday: [meal name] — [brief 1 sentence description]
Wednesday: [meal name] — [brief 1 sentence description]
Thursday: [meal name] — [brief 1 sentence description]
Friday: [meal name] — [brief 1 sentence description]
Saturday: [meal name] — [brief 1 sentence description, can be more involved]
Sunday: [meal name] — [brief 1 sentence description, can be more involved]

LUNCHES:
Monday: [meal]
Tuesday: [meal]
Wednesday: [meal]
Thursday: [meal]
Friday: [meal]

🛒 GROCERY LIST FOR THIS PLAN:
[List every ingredient needed, organized by category:]

PRODUCE:
- item

PROTEINS:
- item

DAIRY & EGGS:
- item

PANTRY & DRY GOODS:
- item

FROZEN:
- item

OTHER:
- item

Keep the grocery list practical — assume Mason has basic staples (salt, pepper, olive oil, garlic, onion, basic spices).
Only list what he actually needs to buy.
"""

    print("[Meal Agent] Generating meal plan...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    full_response = response.content[0].text

    # Split plan from grocery list
    if "🛒 GROCERY LIST" in full_response:
        parts = full_response.split("🛒 GROCERY LIST")
        plan_section = parts[0].strip()
        grocery_section = "🛒 GROCERY LIST" + parts[1]
    else:
        plan_section = full_response
        grocery_section = ""

    # Extract grocery items as a flat list
    grocery_items = []
    if grocery_section:
        for line in grocery_section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                grocery_items.append(line[2:])

    # Save the full plan
    save_meal_plan(full_response)
    print(f"[Meal Agent] Plan saved to meal_plan.txt")

    return {
        "plan": plan_section,
        "grocery_section": grocery_section,
        "grocery_items": grocery_items,
        "full_response": full_response
    }

def get_current_meal_plan():
    """Read and return the current saved meal plan."""
    filepath = os.path.join(DOCUMENTS_PATH, "meal_plan.txt")
    if not os.path.exists(filepath):
        return "No meal plan found. Ask me to generate one!"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    # Test the meal agent directly
    result = generate_meal_plan()
    print(result["full_response"])
