"""
agent.py
--------
Mason's Personal AI Agent — main orchestrator.
Runs the Telegram bot, agent loop, and tool router.
All domain logic lives in agents/ and core/.
"""

import anthropic
import math
import os
import asyncio
from datetime import date
from tavily import TavilyClient
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ── Agent imports ──────────────────────────────────────────────────────────
from agents import calendar_agent, tasks_agent, habits_agent
from agents import lists_agent, chores_agent, briefing_agent
from agents.meal_agent import generate_meal_plan, get_current_meal_plan
from core.config import DOCUMENTS_DIR, GROCERY_CATEGORIES
from core.display import wrap_display

client = anthropic.Anthropic()

# ══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════

tools = [
    # ── Core ──────────────────────────────────────────────────────────────
    {
        "name": "get_current_date",
        "description": "Get today's exact date and year. Always call this tool first before any search involving dates, calendars, or anything time-sensitive.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "web_search_news",
        "description": "Search for recent news and current events from the past week.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The news search query"}},
            "required": ["query"]
        }
    },
    {
        "name": "web_search_general",
        "description": "Search the web for general information, facts, calendar dates, definitions, or anything that is not breaking news.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "description": "Perform mathematical calculations.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression to evaluate"}},
            "required": ["expression"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the documents folder.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string", "description": "Name of file to read"}},
            "required": ["filename"]
        }
    },
    {
        "name": "write_file",
        "description": "Create a new file or overwrite an existing file in the documents folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content":  {"type": "string"}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files available in the documents folder.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "append_to_file",
        "description": "Add new content to the end of an existing file without overwriting it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content":  {"type": "string"}
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "delete_from_file",
        "description": "Remove a specific line from a file in the documents folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename":       {"type": "string"},
                "line_to_delete": {"type": "string"}
            },
            "required": ["filename", "line_to_delete"]
        }
    },
    # ── Tasks (local txt) ─────────────────────────────────────────────────
    {
        "name": "add_task",
        "description": "Add a new task to the local master task list with a category tag and priority level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task":     {"type": "string"},
                "category": {"type": "string", "description": "e.g. PERSONAL, FITNESS, SHOPPING, GENERAL"},
                "priority": {"type": "string", "description": "high, medium, or low"}
            },
            "required": ["task", "category", "priority"]
        }
    },
    {
        "name": "view_tasks",
        "description": "View tasks from the local master task list. Can filter by category or priority.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_by": {"type": "string", "description": "Category, priority level, or 'all'"}
            }
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a local task as complete.",
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"]
        }
    },
    # ── Briefing ──────────────────────────────────────────────────────────
    {
        "name": "get_weather",
        "description": "Get the current weather and today's forecast for Houston, TX.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_daily_briefing",
        "description": "Generate a full daily briefing including weather, news, sports, tasks, and calendar.",
        "input_schema": {"type": "object", "properties": {}}
    },
    # ── Smart Lists ───────────────────────────────────────────────────────
    {
        "name": "list_add",
        "description": "Add an item to one of Mason's named lists: grocery, chores, workout, ai_research, errands, goals_90day, entertainment, gift_ideas, wishlist, restaurants, shower_thoughts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_name": {"type": "string"},
                "item":      {"type": "string"}
            },
            "required": ["list_name", "item"]
        }
    },
    {
        "name": "list_view",
        "description": "View items in one of Mason's named lists. Can filter by tag or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_name": {"type": "string"},
                "filter_by": {"type": "string"}
            },
            "required": ["list_name"]
        }
    },
    {
        "name": "list_remove",
        "description": "Remove a specific item from one of Mason's named lists.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_name": {"type": "string"},
                "item":      {"type": "string"}
            },
            "required": ["list_name", "item"]
        }
    },
    {
        "name": "list_clear",
        "description": "Clear all items from a list.",
        "input_schema": {
            "type": "object",
            "properties": {"list_name": {"type": "string"}},
            "required": ["list_name"]
        }
    },
    {
        "name": "list_show_all",
        "description": "Show a summary of all lists and how many items are in each one.",
        "input_schema": {"type": "object", "properties": {}}
    },
    # ── Chores ────────────────────────────────────────────────────────────
    {
        "name": "get_todays_chores",
        "description": "Get today's chores with completion status (✅ done / ⏳ pending) based on logged history.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "chore_complete",
        "description": "Log a chore as completed today. Use when Mason says 'I vacuumed', 'did laundry', 'mopped', 'changed the AC filter', or any chore completion. Also logs to Google Calendar automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore_name_input": {"type": "string", "description": "The chore that was completed — fuzzy matched against the chore list"},
                "note": {"type": "string", "description": "Optional note e.g. 'both bathrooms', 'replaced with HEPA filter'"}
            },
            "required": ["chore_name_input"]
        }
    },
    {
        "name": "chore_history_view",
        "description": "View chore completion history. Can filter by chore name. Use when Mason asks 'what chores have I done' or 'show my chore log'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore": {"type": "string", "description": "Optional chore name to filter by"},
                "limit": {"type": "integer", "description": "Number of entries to show. Default 20."}
            }
        }
    },
    {
        "name": "chore_last_done",
        "description": "Check when a specific chore was last completed. Use when Mason asks 'when did I last vacuum' or 'when did I last change the AC filter'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore": {"type": "string", "description": "The chore to look up"}
            },
            "required": ["chore"]
        }
    },
    {
        "name": "chore_status_all",
        "description": "Show full status of ALL chores across all frequencies with done/pending indicators and days since last completion. Use for 'show all my chores' or 'what's my chore status'.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "chore_add",
        "description": "Add a new chore to the chore list with a frequency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore_name_input": {"type": "string", "description": "The chore description"},
                "frequency": {"type": "string", "description": "DAILY, WEEKLY-MON, WEEKLY-TUE, WEEKLY-WED, WEEKLY-THU, WEEKLY-FRI, WEEKLY-SAT, WEEKLY-SUN, MONTHLY, QUARTERLY, or ANNUALLY"}
            },
            "required": ["chore_name_input", "frequency"]
        }
    },
    {
        "name": "chore_remove",
        "description": "Remove a chore from the chore list permanently.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore_name_input": {"type": "string", "description": "The chore to remove — fuzzy matched"}
            },
            "required": ["chore_name_input"]
        }
    },
    {
        "name": "reschedule_chore",
        "description": "Move a chore to a new frequency tag.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chore":         {"type": "string"},
                "new_frequency": {"type": "string", "description": "DAILY, WEEKLY-MON … WEEKLY-SUN, MONTHLY, QUARTERLY, ANNUALLY"}
            },
            "required": ["chore", "new_frequency"]
        }
    },
    {
        "name": "get_maintenance_due",
        "description": "Check what home maintenance tasks are due this month, quarter, or year — with completion status.",
        "input_schema": {
            "type": "object",
            "properties": {"period": {"type": "string", "description": "monthly, quarterly, or annually"}},
            "required": ["period"]
        }
    },
    # ── Calendar ──────────────────────────────────────────────────────────
    {
        "name": "calendar_add_event",
        "description": "Add an event to Mason's Google Calendar. Supports recurrence and named calendars. Always use get_day_of_week_date first if user says a day name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string"},
                "date":             {"type": "string", "description": "YYYY-MM-DD"},
                "time":             {"type": "string", "description": "24hr e.g. '19:00'"},
                "duration_minutes": {"type": "integer"},
                "description":      {"type": "string"},
                "calendar_name":    {"type": "string"},
                "recurrence":       {"type": "string", "description": "e.g. 'every wednesday until May 20'"}
            },
            "required": ["title", "date"]
        }
    },
    {
        "name": "calendar_get_events",
        "description": "Get upcoming events from Mason's Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {"days_ahead": {"type": "integer", "description": "Default 7"}}
        }
    },
    {
        "name": "calendar_get_today",
        "description": "Get today's events from Mason's Google Calendar.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_day_of_week_date",
        "description": "Get the exact date for a relative day reference like 'this Wednesday', 'next Monday', 'tomorrow'. Always use before adding calendar events when user says a day name.",
        "input_schema": {
            "type": "object",
            "properties": {"day_reference": {"type": "string"}},
            "required": ["day_reference"]
        }
    },
    {
        "name": "calendar_update_event",
        "description": "Update an existing calendar event. If recurring, will ask Mason 1/2/3.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":          {"type": "string"},
                "new_title":            {"type": "string"},
                "new_date":             {"type": "string"},
                "new_time":             {"type": "string"},
                "new_duration_minutes": {"type": "integer"},
                "calendar_name":        {"type": "string"}
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "calendar_confirm_recurring_update",
        "description": "Apply a pending recurring event update after Mason replies 1, 2, or 3.",
        "input_schema": {
            "type": "object",
            "properties": {"choice": {"type": "string"}},
            "required": ["choice"]
        }
    },
    {
        "name": "calendar_set_recurrence",
        "description": "Set, change, or remove recurrence on an existing calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":             {"type": "string"},
                "recurrence_description":  {"type": "string"},
                "date":                    {"type": "string"},
                "calendar_name":           {"type": "string"}
            },
            "required": ["search_term", "recurrence_description"]
        }
    },
    {
        "name": "calendar_delete_event",
        "description": "Delete an existing calendar event. Confirm first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":   {"type": "string"},
                "date":          {"type": "string"},
                "calendar_name": {"type": "string"}
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "calendar_find_free_time",
        "description": "Find free time slots in Mason's calendar. Returns 2-3 options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_minutes":  {"type": "integer"},
                "date_range_start":  {"type": "string"},
                "date_range_end":    {"type": "string"},
                "hours_start":       {"type": "string"},
                "hours_end":         {"type": "string"}
            },
            "required": ["duration_minutes", "date_range_start", "date_range_end"]
        }
    },
    {
        "name": "calendar_get_event_details",
        "description": "Get details of a specific event — title, time, duration, calendar name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {"type": "string"},
                "date":        {"type": "string"}
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "calendar_add_reminder",
        "description": "Add a reminder to an existing event. Default 30 minutes before.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":    {"type": "string"},
                "minutes_before": {"type": "integer"},
                "date":           {"type": "string"}
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "calendar_move_event",
        "description": "Move an event to a new date/time. Always use get_day_of_week_date first if user says a day name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":          {"type": "string"},
                "new_date":             {"type": "string"},
                "new_time":             {"type": "string"},
                "new_duration_minutes": {"type": "integer"},
                "date":                 {"type": "string"}
            },
            "required": ["search_term", "new_date"]
        }
    },
    {
        "name": "calendar_duplicate_event",
        "description": "Duplicate an existing event to a new date. Always ask which calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term":     {"type": "string"},
                "new_date":        {"type": "string"},
                "new_time":        {"type": "string"},
                "target_calendar": {"type": "string"},
                "date":            {"type": "string"}
            },
            "required": ["search_term", "new_date", "target_calendar"]
        }
    },
    {
        "name": "calendar_bulk_view",
        "description": "View all calendar events grouped by day for a specified date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date":   {"type": "string"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "calendar_set_event_color",
        "description": "Set a color category on an existing calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {"type": "string"},
                "color_name":  {"type": "string", "description": "e.g. Health, Social, Fitness, Family"},
                "date":        {"type": "string"}
            },
            "required": ["search_term", "color_name"]
        }
    },
    {
        "name": "calendar_audit_uncategorized",
        "description": "Scan the next 14 days for events with no color and return suggested colors.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "calendar_smart_schedule",
        "description": "Find the best available time slot for a task before a deadline. Shows the slot first — confirm with calendar_confirm_smart_schedule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title":       {"type": "string"},
                "duration_minutes": {"type": "integer"},
                "deadline_date":    {"type": "string"},
                "hours_start":      {"type": "string"},
                "hours_end":        {"type": "string"},
                "calendar_name":    {"type": "string"}
            },
            "required": ["task_title", "duration_minutes", "deadline_date", "hours_start", "hours_end"]
        }
    },
    {
        "name": "calendar_confirm_smart_schedule",
        "description": "Book the slot suggested by calendar_smart_schedule after Mason says yes.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "calendar_conflict_report",
        "description": "Scan the next 30 days for scheduling conflicts.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "calendar_weekly_prep",
        "description": "Generate Mason's weekly prep report — events needing attention, conflicts, uncategorized items.",
        "input_schema": {"type": "object", "properties": {}}
    },
    # ── Meal Planning ─────────────────────────────────────────────────────
    {
        "name": "generate_meal_plan",
        "description": "Generate a weekly meal plan using the dedicated meal planning agent.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "view_meal_plan",
        "description": "View Mason's current saved meal plan.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "add_meal_groceries",
        "description": "Add the grocery items from the current meal plan to Mason's grocery list.",
        "input_schema": {"type": "object", "properties": {}}
    },
    # ── Habits ────────────────────────────────────────────────────────────
    {
        "name": "habit_log",
        "description": "Log a habit check-in for today. Habits: workout, water, stretching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "habit":     {"type": "string"},
                "completed": {"type": "boolean"},
                "note":      {"type": "string"}
            },
            "required": ["habit", "completed"]
        }
    },
    {
        "name": "habit_view",
        "description": "View habit tracking history. Filter by habit name or time period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "habit":  {"type": "string", "description": "workout, water, stretching, or 'all'"},
                "period": {"type": "string", "description": "today, this_week, last_7_days, or all"}
            }
        }
    },
    {
        "name": "habit_streak",
        "description": "Get the current streak and weekly summary for Mason's habits.",
        "input_schema": {"type": "object", "properties": {}}
    },
    # ── Google Tasks ──────────────────────────────────────────────────────
    {
        "name": "tasks_add",
        "description": "Add a new task to a Google Task list. Use this when Mason says 'add a task', 'create a task', 'remind me to', 'I need to', 'put X on my list', or 'add X to my list'. Use get_day_of_week_date first if Mason mentions a day name for the due date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":     {"type": "string"},
                "list_name": {"type": "string", "description": "Defaults to 'My Tasks'"},
                "notes":     {"type": "string"},
                "due_date":  {"type": "string", "description": "YYYY-MM-DD"},
                "priority":  {"type": "string", "description": "high, medium, or low"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "tasks_view",
        "description": "Show the actual tasks INSIDE a Google Task list. Use whenever Mason asks to see, show, list, or view tasks within a list — e.g. 'what tasks are in my main list', 'show my tasks', 'list out my X list'. If a list name is mentioned pass it as list_name. Do NOT use tasks_list_all for these requests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_name":     {"type": "string", "description": "Name of the list to view tasks inside. Pass what Mason said e.g. 'main', 'My Tasks'."},
                "status_filter": {"type": "string", "description": "needsAction (default), completed, or all"},
                "due_filter":    {"type": "string", "description": "today, this_week, or leave empty"}
            }
        }
    },
    {
        "name": "tasks_complete",
        "description": "Mark a specific Google Task as complete. Use when Mason says 'done', 'complete', 'finished', or 'check off' a task by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_search": {"type": "string"},
                "list_name":    {"type": "string"}
            },
            "required": ["title_search"]
        }
    },
    {
        "name": "tasks_delete",
        "description": "Permanently delete a Google Task. Only when Mason explicitly says 'delete' or 'remove'. Always confirm before deleting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_search": {"type": "string"},
                "list_name":    {"type": "string"}
            },
            "required": ["title_search"]
        }
    },
    {
        "name": "tasks_update",
        "description": "Update a Google Task's title, notes, due date, or priority.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_search":  {"type": "string"},
                "new_title":     {"type": "string"},
                "new_notes":     {"type": "string"},
                "new_due_date":  {"type": "string"},
                "new_priority":  {"type": "string"},
                "list_name":     {"type": "string"}
            },
            "required": ["title_search"]
        }
    },
    {
        "name": "tasks_add_subtask",
        "description": "Add a subtask under an existing parent task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_title":  {"type": "string"},
                "subtask_title": {"type": "string"},
                "list_name":     {"type": "string"}
            },
            "required": ["parent_title", "subtask_title"]
        }
    },
    {
        "name": "tasks_list_all",
        "description": "Show a summary of all Google Task LIST NAMES with counts and overdue flags. Use ONLY when Mason asks what lists exist — e.g. 'what task lists do I have', 'show all my lists'. Do NOT use for 'create a task', 'add a task', or any request to see tasks inside a list.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "tasks_list_create",
        "description": "Create a new Google Task list.",
        "input_schema": {
            "type": "object",
            "properties": {"list_name": {"type": "string"}},
            "required": ["list_name"]
        }
    },
    {
        "name": "tasks_list_delete",
        "description": "Delete an entire Google Task list. Always confirm before deleting.",
        "input_schema": {
            "type": "object",
            "properties": {"list_name": {"type": "string"}},
            "required": ["list_name"]
        }
    },
    {
        "name": "tasks_list_rename",
        "description": "Rename an existing Google Task list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "old_name": {"type": "string"},
                "new_name": {"type": "string"}
            },
            "required": ["old_name", "new_name"]
        }
    },
    {
        "name": "tasks_due_today",
        "description": "Get all tasks due today across every list. Use for 'what's due today', 'what do I need to do today'. Do NOT use tasks_view for this.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "tasks_overdue",
        "description": "Get all overdue tasks across every list. Use for 'what am I behind on', 'what's overdue'. Do NOT use tasks_view for this.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "tasks_due_this_week",
        "description": "Get all tasks due in the next 7 days grouped by day. Use for 'what's due this week', 'what's coming up'. Do NOT use tasks_view for this.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "tasks_search",
        "description": "Search tasks by keyword across all lists.",
        "input_schema": {
            "type": "object",
            "properties": {"keyword": {"type": "string"}},
            "required": ["keyword"]
        }
    },
    {
        "name": "tasks_bulk_complete",
        "description": "Mark multiple tasks complete at once.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_list": {"type": "string", "description": "Comma-separated task titles"},
                "list_name":  {"type": "string"}
            },
            "required": ["title_list"]
        }
    },
    {
        "name": "tasks_weekly_summary",
        "description": "Generate a full weekly tasks summary: overdue, due this week, completed last week.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "tasks_calendar_crosscheck",
        "description": "Cross-reference tasks with due dates against Google Calendar to flag tasks due on fully booked days.",
        "input_schema": {"type": "object", "properties": {}}
    },
]


# ══════════════════════════════════════════════════════════════════════════
# CORE TOOL FUNCTIONS (stay in agent.py — no domain logic)
# ══════════════════════════════════════════════════════════════════════════

def get_current_date():
    try:
        return f"Today is {date.today().strftime('%A, %B %d, %Y')}. The current year is {date.today().year}."
    except Exception as e:
        return f"Error getting date: {str(e)}"

def web_search_news(query):
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = tavily.search(query=query, max_results=5, search_depth="advanced", topic="news", days=7)
        if not results or not results.get("results"):
            return f"No news results found for '{query}'."
        return "\n".join(f"- {r['title']} ({r['url']}): {r['content']}" for r in results["results"])
    except Exception as e:
        return f"Search error: {str(e)}"

def web_search_general(query):
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = tavily.search(query=query, max_results=5, search_depth="advanced")
        if not results or not results.get("results"):
            return f"No results found for '{query}'."
        return "\n".join(f"- {r['title']} ({r['url']}): {r['content']}" for r in results["results"])
    except Exception as e:
        return f"Search error: {str(e)}"

def calculator(expression):
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Cannot divide by zero."
    except SyntaxError:
        return f"Error: '{expression}' is not a valid math expression."
    except Exception as e:
        return f"Calculation error: {str(e)}"

def read_file(filename):
    try:
        if "/" in filename or "\\" in filename:
            return "Error: Filename cannot contain path separators."
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        if not os.path.exists(filepath):
            available = os.listdir(DOCUMENTS_DIR) if os.path.exists(DOCUMENTS_DIR) else []
            return f"Error: '{filename}' not found. Available: {', '.join(available) or 'none'}"
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"File read error: {str(e)}"

def write_file(filename, content):
    try:
        if "/" in filename or "\\" in filename:
            return "Error: Filename cannot contain path separators."
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to '{filename}'."
    except Exception as e:
        return f"File write error: {str(e)}"

def list_files():
    try:
        if not os.path.exists(DOCUMENTS_DIR):
            return "Error: Documents folder does not exist."
        files = os.listdir(DOCUMENTS_DIR)
        return "Files:\n" + "\n".join(f"- {f}" for f in files) if files else "No files found."
    except Exception as e:
        return f"Error: {str(e)}"

def append_to_file(filename, content):
    try:
        if "/" in filename or "\\" in filename:
            return "Error: Filename cannot contain path separators."
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        if not os.path.exists(filepath):
            return f"Error: '{filename}' does not exist. Use write_file to create it first."
        with open(filepath, "a", encoding="utf-8") as f:
            f.write("\n" + content)
        return f"Successfully appended to '{filename}'."
    except Exception as e:
        return f"Append error: {str(e)}"

def delete_from_file(filename, line_to_delete):
    try:
        if "/" in filename or "\\" in filename:
            return "Error: Filename cannot contain path separators."
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        if not os.path.exists(filepath):
            return f"Error: '{filename}' does not exist."
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [l for l in lines if l.strip() != line_to_delete.strip()]
        if len(new_lines) == len(lines):
            return f"No matching line found in '{filename}'."
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return f"Successfully deleted line from '{filename}'."
    except Exception as e:
        return f"Delete error: {str(e)}"

def add_task(task, category, priority):
    try:
        if priority.lower() not in ["high", "medium", "low"]:
            return "Error: Priority must be high, medium, or low."
        filepath = os.path.join(DOCUMENTS_DIR, "tasks.txt")
        entry = f"[{category.upper()}] {task} | priority:{priority.lower()} | status:pending\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Task added: [{category.upper()}] {task} (priority: {priority.lower()})"
    except Exception as e:
        return f"Error adding task: {str(e)}"

def view_tasks(filter_by=None):
    try:
        filepath = os.path.join(DOCUMENTS_DIR, "tasks.txt")
        if not os.path.exists(filepath):
            return "No tasks found."
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if filter_by and filter_by.lower() != "all":
            lines = [l for l in lines if filter_by.lower() in l.lower()]
        else:
            if not filter_by:
                lines = [l for l in lines if "status:pending" in l]
        if not lines:
            return f"No tasks found matching '{filter_by}'."
        lines.sort(key=lambda l: 0 if "priority:high" in l else 1 if "priority:medium" in l else 2)
        content = "Your tasks:\n" + "\n".join(f"- {l}" for l in lines)
        return wrap_display(content)
    except Exception as e:
        return f"Error viewing tasks: {str(e)}"

def complete_task(task):
    try:
        filepath = os.path.join(DOCUMENTS_DIR, "tasks.txt")
        if not os.path.exists(filepath):
            return "Error: No task list found."
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        updated = False
        new_lines = []
        for line in lines:
            if task.lower() in line.lower() and "status:pending" in line:
                line = line.replace("status:pending", "status:done")
                updated = True
            new_lines.append(line)
        if not updated:
            return f"No pending task matching '{task}' was found."
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return f"Task marked as complete: {task}"
    except Exception as e:
        return f"Error completing task: {str(e)}"

def agent_generate_meal_plan():
    try:
        result = generate_meal_plan()
        temp_path = os.path.join(DOCUMENTS_DIR, "meal_plan_groceries_pending.txt")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(result["grocery_items"]))
        plan_content = (
            f"{result['plan']}\n\n---\n"
            f"I have {len(result['grocery_items'])} grocery items ready. "
            f"Say 'yes add groceries' to add them to your list."
        )
        return wrap_display(plan_content)
    except Exception as e:
        return f"Error generating meal plan: {str(e)}"

def agent_view_meal_plan():
    try:
        full = get_current_meal_plan()
        if "🛒 GROCERY LIST" in full:
            full = full.split("🛒 GROCERY LIST")[0].strip()
        return wrap_display(full)
    except Exception as e:
        return f"Error viewing meal plan: {str(e)}"

def agent_add_meal_groceries():
    try:
        temp_path    = os.path.join(DOCUMENTS_DIR, "meal_plan_groceries_pending.txt")
        grocery_path = os.path.join(DOCUMENTS_DIR, "grocery.txt")
        if not os.path.exists(temp_path):
            plan  = get_current_meal_plan()
            items = [l[2:].strip() for l in plan.split("\n") if l.strip().startswith("- ")]
        else:
            with open(temp_path, "r", encoding="utf-8") as f:
                items = [l.strip() for l in f.readlines() if l.strip()]
        if not items:
            return "No grocery items found. Generate a meal plan first."
        categorized = []
        for item in items:
            cat = lists_agent.guess_grocery_category(item) or lists_agent.categorize_with_claude(item)
            if cat not in GROCERY_CATEGORIES:
                cat = "Pantry"
            categorized.append(f"[{cat}] {item}")
        with open(grocery_path, "a", encoding="utf-8") as f:
            for item in categorized:
                f.write(item + "\n")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return f"✅ Added {len(categorized)} categorized items to your grocery list!"
    except Exception as e:
        return f"Error adding groceries: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY — replaces the if/elif chain
# ══════════════════════════════════════════════════════════════════════════

def build_registry():
    ca = calendar_agent
    ta = tasks_agent
    ha = habits_agent
    la = lists_agent
    ch = chores_agent
    ba = briefing_agent

    return {
        # Core
        "get_current_date":    lambda i: get_current_date(),
        "web_search_news":     lambda i: web_search_news(i["query"]),
        "web_search_general":  lambda i: web_search_general(i["query"]),
        "calculator":          lambda i: calculator(i["expression"]),
        "read_file":           lambda i: read_file(i["filename"]),
        "write_file":          lambda i: write_file(i["filename"], i["content"]),
        "list_files":          lambda i: list_files(),
        "append_to_file":      lambda i: append_to_file(i["filename"], i["content"]),
        "delete_from_file":    lambda i: delete_from_file(i["filename"], i["line_to_delete"]),
        # Local tasks
        "add_task":            lambda i: add_task(i["task"], i["category"], i["priority"]),
        "view_tasks":          lambda i: view_tasks(i.get("filter_by")),
        "complete_task":       lambda i: complete_task(i["task"]),
        # Briefing
        "get_weather":         lambda i: ba.get_weather(),
        "get_daily_briefing":  lambda i: ba.get_daily_briefing(),
        # Lists
        "list_add":            lambda i: la.list_add(i["list_name"], i["item"]),
        "list_view":           lambda i: la.list_view(i["list_name"], i.get("filter_by")),
        "list_remove":         lambda i: la.list_remove(i["list_name"], i["item"]),
        "list_clear":          lambda i: la.list_clear(i["list_name"]),
        "list_show_all":       lambda i: la.list_show_all(),
        # Chores
        "get_todays_chores":   lambda i: ch.get_todays_chores(),
        "chore_complete":      lambda i: ch.chore_complete(i["chore_name_input"], i.get("note")),
        "chore_history_view":  lambda i: ch.chore_history_view(i.get("chore"), i.get("limit", 20)),
        "chore_last_done":     lambda i: ch.chore_last_done(i["chore"]),
        "chore_status_all":    lambda i: ch.chore_status_all(),
        "chore_add":           lambda i: ch.chore_add(i["chore_name_input"], i["frequency"]),
        "chore_remove":        lambda i: ch.chore_remove(i["chore_name_input"]),
        "reschedule_chore":    lambda i: ch.reschedule_chore(i["chore"], i["new_frequency"]),
        "get_maintenance_due": lambda i: ch.get_maintenance_due(i["period"]),
        # Calendar
        "calendar_add_event":              lambda i: ca.calendar_add_event(i["title"], i["date"], i.get("time"), i.get("duration_minutes", 60), i.get("description"), i.get("calendar_name"), i.get("recurrence")),
        "calendar_get_events":             lambda i: ca.calendar_get_events(i.get("days_ahead", 7)),
        "calendar_get_today":              lambda i: ca.calendar_get_today(),
        "get_day_of_week_date":            lambda i: ca.get_day_of_week_date(i["day_reference"]),
        "calendar_update_event":           lambda i: ca.calendar_update_event(i["search_term"], i.get("new_title"), i.get("new_date"), i.get("new_time"), i.get("new_duration_minutes"), i.get("calendar_name")),
        "calendar_confirm_recurring_update": lambda i: ca.calendar_confirm_recurring_update(i["choice"]),
        "calendar_set_recurrence":         lambda i: ca.calendar_set_recurrence(i["search_term"], i["recurrence_description"], i.get("date"), i.get("calendar_name")),
        "calendar_delete_event":           lambda i: ca.calendar_delete_event(i["search_term"], i.get("date"), i.get("calendar_name")),
        "calendar_find_free_time":         lambda i: ca.calendar_find_free_time(i["duration_minutes"], i["date_range_start"], i["date_range_end"], i.get("hours_start", "08:00"), i.get("hours_end", "21:00")),
        "calendar_get_event_details":      lambda i: ca.calendar_get_event_details(i["search_term"], i.get("date")),
        "calendar_add_reminder":           lambda i: ca.calendar_add_reminder(i["search_term"], i.get("minutes_before", 30), i.get("date")),
        "calendar_move_event":             lambda i: ca.calendar_move_event(i["search_term"], i["new_date"], i.get("new_time"), i.get("new_duration_minutes"), i.get("date")),
        "calendar_duplicate_event":        lambda i: ca.calendar_duplicate_event(i["search_term"], i["new_date"], i["target_calendar"], i.get("new_time"), i.get("date")),
        "calendar_bulk_view":              lambda i: ca.calendar_bulk_view(i["start_date"], i["end_date"]),
        "calendar_set_event_color":        lambda i: ca.calendar_set_event_color(i["search_term"], i["color_name"], i.get("date")),
        "calendar_audit_uncategorized":    lambda i: ca.calendar_audit_uncategorized(),
        "calendar_smart_schedule":         lambda i: ca.calendar_smart_schedule(i["task_title"], i["duration_minutes"], i["deadline_date"], i["hours_start"], i["hours_end"], i.get("calendar_name")),
        "calendar_confirm_smart_schedule": lambda i: ca.calendar_confirm_smart_schedule(),
        "calendar_conflict_report":        lambda i: ca.calendar_conflict_report(),
        "calendar_weekly_prep":            lambda i: ca.calendar_weekly_prep(),
        # Meal planning
        "generate_meal_plan":  lambda i: agent_generate_meal_plan(),
        "view_meal_plan":      lambda i: agent_view_meal_plan(),
        "add_meal_groceries":  lambda i: agent_add_meal_groceries(),
        # Habits
        "habit_log":           lambda i: ha.habit_log(i["habit"], i["completed"], i.get("note")),
        "habit_view":          lambda i: ha.habit_view(i.get("habit"), i.get("period")),
        "habit_streak":        lambda i: ha.habit_streak(),
        # Google Tasks
        "tasks_add":                  lambda i: ta.tasks_add(i["title"], i.get("list_name"), i.get("notes"), i.get("due_date"), i.get("priority")),
        "tasks_view":                 lambda i: ta.tasks_view(i.get("list_name"), i.get("status_filter", "needsAction"), i.get("due_filter")),
        "tasks_complete":             lambda i: ta.tasks_complete(i["title_search"], i.get("list_name")),
        "tasks_delete":               lambda i: ta.tasks_delete(i["title_search"], i.get("list_name")),
        "tasks_update":               lambda i: ta.tasks_update(i["title_search"], i.get("new_title"), i.get("new_notes"), i.get("new_due_date"), i.get("new_priority"), i.get("list_name")),
        "tasks_add_subtask":          lambda i: ta.tasks_add_subtask(i["parent_title"], i["subtask_title"], i.get("list_name")),
        "tasks_list_all":             lambda i: ta.tasks_list_all(),
        "tasks_list_create":          lambda i: ta.tasks_list_create(i["list_name"]),
        "tasks_list_delete":          lambda i: ta.tasks_list_delete(i["list_name"]),
        "tasks_list_rename":          lambda i: ta.tasks_list_rename(i["old_name"], i["new_name"]),
        "tasks_due_today":            lambda i: ta.tasks_due_today(),
        "tasks_overdue":              lambda i: ta.tasks_overdue(),
        "tasks_due_this_week":        lambda i: ta.tasks_due_this_week(),
        "tasks_search":               lambda i: ta.tasks_search(i["keyword"]),
        "tasks_bulk_complete":        lambda i: ta.tasks_bulk_complete(i["title_list"], i.get("list_name")),
        "tasks_weekly_summary":       lambda i: ta.tasks_weekly_summary(),
        "tasks_calendar_crosscheck":  lambda i: ta.tasks_calendar_crosscheck(),
    }

TOOL_REGISTRY = build_registry()


def run_tool(tool_name, tool_input):
    fn = TOOL_REGISTRY.get(tool_name)
    if fn:
        return fn(tool_input)
    return f"Unknown tool: {tool_name}"


# ══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are Mason's personal AI agent based in Houston, TX. "
    "Keep responses short and casual like a text message unless detail is needed. "
    "For any question involving dates, times, or current events, always use the get_current_date tool first. Never assume what year it is. "
    "When generating a daily briefing use get_daily_briefing and format with emoji section headers. "

    "Mason has these named lists: grocery, chores, workout, ai_research, errands, goals_90day, "
    "entertainment (tags: [SHOW]/[MOVIE]/[BOOK]/[PODCAST]/[GAME]), gift_ideas, wishlist (tags: [HOME]/[PERSONAL]), "
    "restaurants, shower_thoughts. "
    "The grocery list is organized into categories: Frozen, Meat, Produce, Spices/Condiments, Pantry, Dairy/Deli, Pet, NonFood. "

    "CRITICAL DISPLAY RULES: (1) When any tool returns list or data, display the COMPLETE raw text exactly as returned — never summarize. "
    "(2) When generate_meal_plan or view_meal_plan returns a meal plan, display it word for word, then ask about groceries. "
    "(3) When Mason says 'yes add groceries' use add_meal_groceries. "

    "HABIT RULES: Mason tracks 3 habits: workout, water, stretching. "
    "When Mason says 'I worked out', 'did my stretching', 'drank water today' use habit_log with completed=true. "
    "When he says 'skipped my workout' use habit_log with completed=false. For streaks use habit_streak. "

    "CHORES RULES: Mason has a chore schedule with frequency tags (daily, weekly, monthly, quarterly, annually). "
    "(1) When Mason says he completed a chore — 'I vacuumed', 'did laundry', 'mopped', 'changed the AC filter', 'cleaned bathrooms' — use chore_complete. "
    "(2) Use get_todays_chores to show today's chores with ✅/⏳ status. "
    "(3) Use chore_status_all for a full overview of all chores. "
    "(4) Use chore_last_done when Mason asks 'when did I last X'. "
    "(5) Use chore_history_view to show the completion log. "
    "(6) Use chore_add to add new chores, chore_remove to remove them. "
    "(7) Completed chores are automatically logged to Google Calendar as Graphite all-day events. "

    "TASKS RULES: Mason uses Google Tasks for structured to-do management. "
    "(1) When Mason says 'add a task' or 'remind me to' use tasks_add. "
    "(2) When Mason asks to see tasks INSIDE a list use tasks_view — never tasks_list_all. "
    "(3) When a day name is mentioned for a due date, ALWAYS call get_day_of_week_date first. "
    "(4) Use tasks_due_today for 'what's due today', tasks_overdue for overdue, tasks_due_this_week for the week ahead. "
    "(5) tasks_list_all is ONLY for 'what lists do I have' — not for viewing tasks. "
    "(6) tasks_weekly_summary gives a full weekly overview. "
    "(7) tasks_calendar_crosscheck finds tasks due on fully booked calendar days. "

    "CALENDAR RULES: "
    "(1) When user mentions a day by name — ALWAYS call get_day_of_week_date FIRST. Never compute dates in your head. "
    "(2) When user mentions a specific calendar name like 'Taco Tuesday', pass it as calendar_name. "
    "(3) If a conflict is found report it and ask what to do. "
    "(4) To add recurring events use calendar_add_event with recurrence parameter. "
    "(5) To change recurrence use calendar_set_recurrence. "
    "(6) To modify events use calendar_update_event — if recurring ask Mason 1/2/3, then calendar_confirm_recurring_update. "
    "(7) To delete use calendar_delete_event — confirm first. "
    "(8) To find free time use calendar_find_free_time. "
    "(9) To move an event use calendar_move_event. "
    "(10) To duplicate use calendar_duplicate_event — always ask which calendar. "
    "(11) To view a date range use calendar_bulk_view. "
    "(12) Colors auto-apply when events are added. "
    "(13) For smart scheduling use calendar_smart_schedule — show slot first, then calendar_confirm_smart_schedule when Mason says yes. "
    "(14) For conflict report use calendar_conflict_report. "
    "(15) For weekly prep use calendar_weekly_prep. "
    "(16) When Mason says 'apply suggested colors' run calendar_audit_uncategorized then apply colors to each uncolored event."
)


# ══════════════════════════════════════════════════════════════════════════
# AGENT LOOP
# ══════════════════════════════════════════════════════════════════════════

def run_agent_conversational(messages):
    print("-" * 50)
    working_messages = list(messages)
    max_steps = 10
    step = 0

    while step < max_steps:
        step += 1
        print("\nClaude is thinking...")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            system=SYSTEM_PROMPT,
            messages=working_messages
        )

        stop_reason = response.stop_reason
        print(f"Stop reason: {stop_reason}")

        if step >= max_steps:
            return "Step limit reached."

        if stop_reason == "end_turn":
            final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
            print(f"\nAgent: {final_text}")
            return final_text

        if stop_reason == "tool_use":
            working_messages.append({"role": "assistant", "content": response.content})
            tool_results      = []
            raw_display_blocks = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"\nClaude wants to use tool: {block.name}")
                    result = run_tool(block.name, block.input)
                    print(f"  [RESULT] {str(result)[:200]}...")

                    if "[DISPLAY_RAW]" in result and "[/DISPLAY_RAW]" in result:
                        raw_start = result.index("[DISPLAY_RAW]") + len("[DISPLAY_RAW]")
                        raw_end   = result.index("[/DISPLAY_RAW]")
                        raw_display_blocks.append(result[raw_start:raw_end].strip())
                        result = f"[Data displayed directly to Mason — {len(raw_display_blocks[-1])} chars shown verbatim]"

                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })

            if raw_display_blocks:
                combined = "\n\n".join(raw_display_blocks)
                working_messages.append({"role": "user", "content": tool_results})
                step += 1
                followup = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=200,
                    tools=tools,
                    system=(
                        "You are Mason's personal AI agent. The data was already displayed to Mason directly. "
                        "Only add a follow-up if Mason asked a direct question that the data did not answer, "
                        "or if there is a required action to confirm. "
                        "If the tool returned a complete list, view, or log — say nothing. "
                        "Do not offer help, do not summarize, do not add commentary."
                    ),
                    messages=working_messages
                )
                followup_text = "".join(
                    b.text.strip() for b in followup.content if hasattr(b, "text") and b.text.strip()
                )
                final = combined + (f"\n\n{followup_text}" if followup_text else "")
                print(f"\nAgent (DISPLAY_RAW): {final[:200]}...")
                return final

            working_messages.append({"role": "user", "content": tool_results})


# ══════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ══════════════════════════════════════════════════════════════════════════

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

conversation_histories = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id      = str(update.effective_chat.id)
    user_message = update.message.text

    if chat_id != TELEGRAM_CHAT_ID:
        await update.message.reply_text("Unauthorized.")
        return

    print(f"\n[Telegram] You: {user_message}")

    if chat_id not in conversation_histories:
        conversation_histories[chat_id] = []

    conversation_histories[chat_id].append({"role": "user", "content": user_message})
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    response_text = run_agent_conversational(conversation_histories[chat_id])
    conversation_histories[chat_id].append({"role": "assistant", "content": response_text})

    if len(response_text) <= 4096:
        await update.message.reply_text(response_text)
    else:
        for chunk in [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]:
            await update.message.reply_text(chunk)


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return
    if not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_CHAT_ID is not set.")
        return

    print("=== Mason's Personal Agent ===")
    print("Telegram bot is running. Message your bot to get started!")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()