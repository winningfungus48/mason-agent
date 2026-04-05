"""
core/config.py
--------------
Central configuration for Mason's Personal Agent.
All hardcoded values live here. Change once, updates everywhere.
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
TOKEN_PATH    = os.path.join(BASE_DIR, "token.json")
CREDS_PATH    = os.path.join(BASE_DIR, "credentials.json")

# ── Timezone ───────────────────────────────────────────────────────────────
TIMEZONE = "America/Chicago"

# ── Google API Scopes ──────────────────────────────────────────────────────
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]

# ── Habits ─────────────────────────────────────────────────────────────────
HABITS     = ["workout", "water", "stretching"]
HABIT_FILE = os.path.join(DOCUMENTS_DIR, "habits.txt")

# ── Smart Lists ────────────────────────────────────────────────────────────
LISTS = {
    "grocery":       "grocery.txt",
    "chores":        "chores.txt",
    "workout":       "workout.txt",
    "ai_research":   "ai_research.txt",
    "errands":       "errands.txt",
    "goals_90day":   "goals_90day.txt",
    "entertainment": "entertainment.txt",
    "gift_ideas":    "gift_ideas.txt",
    "wishlist":      "wishlist.txt",
    "restaurants":   "restaurants.txt",
    "shower_thoughts": "shower_thoughts.txt",
}

GROCERY_CATEGORIES = [
    "Frozen", "Meat", "Produce", "Spices/Condiments",
    "Pantry", "Dairy/Deli", "Pet", "NonFood",
]

# ── Briefing ───────────────────────────────────────────────────────────────
SPORTS_TEAMS = (
    "Texas A&M Aggies | Houston Texans | Houston Astros | "
    "Houston Rockets | Philadelphia Phillies | Indianapolis Colts"
)
CITY_NEWS_QUERY = (
    "College Station TX OR Canyon Lake TX OR Milwaukee WI OR Fort Worth TX news today"
)

# ── Chore Scheduler ────────────────────────────────────────────────────────
QUARTERLY_MONTHS = [1, 4, 7, 10]   # Jan, Apr, Jul, Oct
ANNUAL_MONTHS    = [1]              # January

WEEKDAY_TAGS = {
    0: "WEEKLY-MON", 1: "WEEKLY-TUE", 2: "WEEKLY-WED",
    3: "WEEKLY-THU", 4: "WEEKLY-FRI", 5: "WEEKLY-SAT", 6: "WEEKLY-SUN",
}

# ── Calendar Color Map ─────────────────────────────────────────────────────
COLOR_CATEGORY_MAP = {
    "health":      {"id": "11", "name": "Tomato",    "emoji": "🔴"},
    "medical":     {"id": "11", "name": "Tomato",    "emoji": "🔴"},
    "social":      {"id": "6",  "name": "Tangerine", "emoji": "🟠"},
    "event":       {"id": "6",  "name": "Tangerine", "emoji": "🟠"},
    "errands":     {"id": "5",  "name": "Banana",    "emoji": "🟡"},
    "personal":    {"id": "5",  "name": "Banana",    "emoji": "🟡"},
    "fitness":     {"id": "10", "name": "Basil",     "emoji": "🟢"},
    "workout":     {"id": "10", "name": "Basil",     "emoji": "🟢"},
    "gym":         {"id": "10", "name": "Basil",     "emoji": "🟢"},
    "important":   {"id": "9",  "name": "Blueberry", "emoji": "🔵"},
    "work":        {"id": "9",  "name": "Blueberry", "emoji": "🔵"},
    "family":      {"id": "3",  "name": "Grape",     "emoji": "🟣"},
    "routine":     {"id": "8",  "name": "Graphite",  "emoji": "⚫"},
    "recurring":   {"id": "8",  "name": "Graphite",  "emoji": "⚫"},
    "birthday":    {"id": "4",  "name": "Flamingo",  "emoji": "🩷"},
    "anniversary": {"id": "4",  "name": "Flamingo",  "emoji": "🩷"},
    "travel":      {"id": "7",  "name": "Peacock",   "emoji": "🩵"},
    "trip":        {"id": "7",  "name": "Peacock",   "emoji": "🩵"},
}

COLOR_KEYWORDS = {
    "health":    ["doctor", "dentist", "physician", "hospital", "clinic", "checkup",
                  "therapy", "vet", "vaccine", "prescription"],
    "social":    ["party", "dinner", "lunch", "brunch", "happy hour", "wedding",
                  "reception", "gathering", "game night", "watch party", "concert", "show"],
    "fitness":   ["gym", "workout", "run", "golf", "tennis", "swim", "yoga",
                  "crossfit", "bike", "hike", "lesson", "training"],
    "family":    ["mom", "dad", "sister", "brother", "family", "kids",
                  "parent", "grandma", "grandpa"],
    "birthday":  ["birthday", "bday", "anniversary"],
    "routine":   ["flea", "tick", "heartworm", "medication", "filter",
                  "oil change", "maintenance"],
    "travel":    ["flight", "hotel", "trip", "vacation", "airport", "cruise", "travel"],
    "important": ["interview", "deadline", "meeting", "presentation",
                  "appointment", "closing", "signing"],
}
