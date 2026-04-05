# Personal Agent - Step by Step

---

## AI Agent Weekend Guide — Original Steps

---

### Saturday Morning: Set Up Your Tools *(~2 hours)*

**Step 1: Get Claude API Access**
- Go to console.anthropic.com and create an account
- Add billing and retrieve your API key
- Cost is very cheap for personal use — a full weekend of testing runs a few dollars at most

**Step 2: Install Python**
- Go to python.org and download the latest version
- After installing, open your terminal and confirm it works by typing:
  ```
  python --version
  ```
- On Windows: use Command Prompt or PowerShell. On Mac: use Terminal.

**Step 3: Set Up Your Project**
- Run these commands one at a time in your terminal:
  ```bash
  mkdir my-first-agent
  cd my-first-agent
  python -m venv venv
  venv\Scripts\activate        # Windows
  # source venv/bin/activate   # Mac/Linux
  pip install anthropic
  ```
- You now have a project folder with the Anthropic library installed

---

### Saturday Afternoon: Build the Agent Brain *(~3 hours)*

**How the Agent Loop Works**
Every agent follows the same basic loop:
1. Send a goal to Claude along with descriptions of available tools
2. Claude decides whether it needs to use a tool to achieve the goal
3. If yes, Claude tells you which tool to call and with what inputs
4. Your code executes the tool and sends the result back to Claude
5. Claude decides if it needs another tool or if the goal is achieved
6. Repeat until done

**Step 4: Build a Simple Agent**
- Create a new file called `agent.py` in your project folder
- Use Claude to generate the starter code with two tools: a simulated web search and a calculator
- Set your API key as an environment variable before running:
  ```bash
  set ANTHROPIC_API_KEY=your-key-here     # Windows
  # export ANTHROPIC_API_KEY=your-key-here  # Mac/Linux
  ```
- Run the agent:
  ```bash
  python agent.py
  ```
- Test it with: *"What is 15 percent of 847 and is that a normal tip amount?"*
- You should see the agent think, use the calculator tool, and deliver a final answer

---

### Saturday Evening: Add Real Tools *(~2 hours)*

**Step 5: Add a Real Web Search Tool**
- Sign up at tavily.com for a free API key
- Install the Tavily library: `pip install tavily-python`
- Set your Tavily key: `set TAVILY_API_KEY=your-key-here`
- Replace the mock search function in agent.py with a real Tavily search function
- Use `search_depth="advanced"`, `topic="news"`, and `days=7` for recent results
- Add a second general search tool (without `topic="news"`) for non-news queries
- Test with a real current events question — it should now pull live data

**Step 6: Add a File Reading Tool**
- Create a `documents` folder inside your project: `mkdir documents`
- Add a `notes.txt` file with sample content to test with
- Add a `read_file` tool to agent.py that reads files from the documents folder
- Test with: *"Read my notes.txt and summarize the key action items"*
- Try combining tools: *"Read my notes.txt and search the web to find out if May 1st is a holiday"*

---

### Sunday Morning: Make It Conversational *(~2 hours)*

**Step 7: Add Conversation Memory**
- Add a `conversation_history` list that persists across messages
- Wrap the agent in a `while True` loop with a `quit` command to exit
- Create a new function `run_agent_conversational` that takes the full history each time
- After each exchange, append both the user message and agent response to history
- Test by asking follow-up questions that reference earlier answers — the agent should remember
- Key insight: Claude has no built-in memory — the "memory" is just the full history sent with every API call

**Step 8: Add Error Handling**
- Wrap every tool function in try/except blocks
- Add API key presence checks to both search tools
- Add specific exception types to the calculator (ZeroDivisionError, SyntaxError)
- Add path security check to read_file (prevent reading files outside documents folder)
- Add file listing fallback — if a file isn't found, tell Claude what files ARE available
- Add a step limit (max_steps = 10) to prevent infinite loops
- Test by asking for a file that doesn't exist — should return available files, not crash

---

### Sunday Afternoon: Polish and Test *(~2 hours)*

**Step 9: Test With Real Tasks**
Run at least 10 different goals ranging from simple to complex:
- *"What is the compound interest on $10,000 at 5% over 10 years?"*
- *"Read my notes.txt and list the action items"*
- *"What are the latest AI news stories this week?"*
- *"Search the web and summarize what is happening with tariffs right now"*
- *"Read my notes.txt and search the web for news related to any of the action items"*
- *"What day is Memorial Day this year and how many days away is it?"*
- *"Calculate hello divided by world"* (error handling test)
- *"Read my shopping_list.txt"* (missing file test)

Watch where it works well and where it struggles. Every failure is a signal for improvement.

**Step 10: Add Your Own Custom Tool**
- Think of one task you do repeatedly in your life
- Build a Python function for it
- Add it to the tools list with a clear description
- Connect it in run_tool
- Test it with a real goal

---

### Additional Improvements Made During Build

**get_current_date Tool**
- Added a dedicated tool that returns today's exact date
- Solves the problem of Claude defaulting to training data years (e.g. 2024) when answering time-sensitive questions
- System prompt instructs Claude to always call this tool first before any date-related search
- Dynamic using Python's `date.today()` — never needs manual updating

**launch_agent.bat**
- Created a Windows batch file to launch the agent with one double-click
- Automatically navigates to the project folder, activates the virtual environment, sets both API keys, and runs agent.py
- Eliminates the need to manually set environment variables every session

---

## Personal Agent — Build Order

---

### Phase 1: Foundational File Tools ✅ COMPLETE

**Tools Built:**
- `write_file` — creates or overwrites a file in the documents folder
- `list_files` — lists all files in the documents folder
- `append_to_file` — adds content to end of existing file without overwriting
- `delete_from_file` — removes a specific line from a file

**Implementation Details:**
- All four tools added to the `tools` list in agent.py
- All four functions added with full error handling (permission errors, missing files, path security)
- All four wired into `run_tool` router
- Security check added to prevent path traversal (no `/` or `\` in filenames)

**Tests Passed:**
- ✅ list_files — listed all files in documents folder
- ✅ write_file — created shopping.txt with items
- ✅ append_to_file — added items to shopping.txt
- ✅ delete_from_file — removed a specific item from shopping.txt
- ✅ Combined — read notes.txt, summarized action items, saved to action_summary.txt

---

### Phase 2: Task & Reminder System ✅ COMPLETE

**Tools Built:**
- `add_task` — adds a task with category tag and priority level to tasks.txt
- `view_tasks` — views all pending tasks, filterable by category or priority, sorted by priority
- `complete_task` — marks a task as done in tasks.txt

**Task File Structure:**
```
[PERSONAL] Call the dentist | priority:high | status:pending
[FITNESS] Go for a run | priority:medium | status:pending
[SHOPPING] Buy new headphones | priority:low | status:pending
```

**Implementation Details:**
- Single master tasks.txt file with category tags and priority levels
- Tasks auto-sorted high → medium → low when viewed
- Completed tasks stay in file with status:done (full history preserved)
- Default view shows only pending tasks unless filter_by="all"
- Google Calendar and Tasks integration deferred to later phase

**Tests Passed:**
- ✅ add_task — added multiple tasks with categories and priorities
- ✅ view_tasks — showed all pending tasks sorted by priority
- ✅ view_tasks with filter — filtered by category and by priority level
- ✅ complete_task — marked a task as done
- ✅ Confirmed completed task removed from pending view

---

### Phase 3: Daily Briefing ✅ COMPLETE

**Tools Built:**
- `get_weather` — fetches current Houston weather forecast
- `get_daily_briefing` — generates full personalized daily briefing with 10 sections

**Briefing Sections:**
- 📅 Date
- 🌤 Weather — Houston TX, short bullet points
- 🚨 Breaking / Major News — detailed summaries
- 🌍 World News — detailed summaries
- 🏙 Houston Local News — detailed summaries
- 📍 City News — College Station, Canyon Lake, Milwaukee, Fort Worth (labeled per city)
- 🤖 Tech & AI News — detailed summaries
- 🚀 AI Companies & Product News — new launches, features, announcements
- 💡 AI Tip of the Day
- 🏈 Sports — bullet points grouped by team (Texas A&M / Texans / Astros / Rockets / Phillies / Colts)
- 🗓 This Week at a Glance — upcoming events and deadlines
- ✅ Pending Tasks — sorted high → medium → low priority

**Implementation Details:**
- Single `get_daily_briefing` tool makes 10 parallel Tavily searches
- Internal `search()` helper function reduces code repetition
- max_tokens increased to 4096 to support detailed briefing output
- System prompt updated with exact emoji-labeled formatting instructions per section
- On-demand via natural language ("give me my briefing", "morning update", etc.)

**Tests Passed:**
- ✅ Weather only query
- ✅ Full daily briefing on demand
- ✅ All sections rendered with correct formatting

---

### Phase 4: Telegram Bot Interface ✅ COMPLETE

**Files Created/Modified:**
- `agent.py` — terminal input replaced with Telegram bot interface
- `briefing_scheduler.py` — standalone script for automated 6AM morning briefing
- `launch_agent.bat` — updated with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env variables

**Implementation Details:**
- Bot created via BotFather in Telegram
- Security check — bot only responds to Mason's chat ID, rejects all others
- Conversation history maintained per chat ID
- Long responses auto-split into chunks (Telegram has 4096 char limit per message)
- Typing indicator shown while agent is thinking
- Morning briefing automated via Windows Task Scheduler at 6:00 AM daily
- `briefing_scheduler.py` imports agent and runs a briefing request, sends result to Telegram

**Setup Steps Completed:**
- ✅ Telegram downloaded and account created
- ✅ Bot created via BotFather
- ✅ Bot token generated and saved
- ✅ Chat ID retrieved via getUpdates API
- ✅ python-telegram-bot library installed
- ✅ Bot token reset after being accidentally exposed in chat
- ✅ All keys added to launch_agent.bat
- ✅ Task Scheduler configured for 6:00 AM daily briefing

---

### Phase 5: Smart List Manager ✅ COMPLETE

**Tools Built:**
- `list_add` — adds item to a named list with optional category tags
- `list_view` — views a list with optional tag filter; grocery shows grouped by category
- `list_remove` — removes a specific item from a list
- `list_clear` — clears all items from a list
- `list_show_all` — shows all lists with item counts

**Lists Available:**
- 🛒 grocery — categorized by: Frozen, Meat, Produce, Spices/Condiments, Pantry, Dairy/Deli, Pet, NonFood
- 🏠 chores
- 💪 workout
- 🤖 ai_research
- 🏃 errands
- 🎯 goals_90day
- 🎬 entertainment — tags: [SHOW], [MOVIE], [BOOK], [PODCAST], [GAME]
- 🎁 gift_ideas — tag: [PERSON NAME]
- 🛍️ wishlist — tags: [HOME], [PERSONAL]
- 🍽️ restaurants
- 💡 shower_thoughts

**Implementation Details:**
- Grocery items auto-categorized using keyword matching + Claude fallback
- All lists stored as .txt files in documents folder
- Natural language interaction: "add milk to grocery", "show my entertainment list"

---

### Phase 6: Chore & Home Maintenance Schedule ✅ COMPLETE

**Tools Built:**
- `get_todays_chores` — returns daily chores + today's weekly chores + any monthly/quarterly/annual items due
- `reschedule_chore` — moves a chore to a different frequency tag
- `get_maintenance_due` — returns all maintenance items for a given period

**Implementation Details:**
- Chores organized by frequency tags: [DAILY], [WEEKLY-SAT], [WEEKLY-SUN], [MONTHLY], [QUARTERLY], [ANNUALLY]
- Starter chores.txt auto-created on first run with common household tasks
- Push reminders via chore_scheduler.py on Saturdays and Sundays
- Monthly reminders on 1st of each month, quarterly on Jan/Apr/Jul/Oct, annual in January
- Chore reminder scheduler added to Windows Task Scheduler

**Tests Passed:**
- ✅ get_todays_chores — returned correct daily and weekly chores
- ✅ reschedule_chore — moved a chore to a different day
- ✅ get_maintenance_due — returned quarterly maintenance items

---

### Phase 7: Google Calendar Integration ✅ COMPLETE

**Core Tools Built:**
- `calendar_add_event` — creates timed or all-day events, supports recurrence, auto-applies color
- `calendar_get_events` — fetches upcoming events across all calendars
- `calendar_get_today` — fetches today's events in Houston timezone
- `calendar_update_event` — updates events, handles recurring series with 1/2/3 choice
- `calendar_confirm_recurring_update` — applies pending recurring update after Mason's choice
- `calendar_delete_event` — deletes events with confirmation
- `calendar_set_recurrence` — set/change/remove recurrence using natural language RRULE converter
- `calendar_move_event` — moves event to new date/time preserving all details
- `calendar_duplicate_event` — copies event to new date, always asks which calendar
- `calendar_bulk_view` — shows events grouped by day for any date range
- `calendar_find_free_time` — returns 2-3 free slot options of minimum 30 minutes
- `calendar_get_event_details` — returns title, time, duration, calendar name
- `calendar_add_reminder` — adds popup reminder, default 30 minutes
- `calendar_set_event_color` — sets color by category name
- `calendar_auto_categorize` — auto-applies colors silently when events are added
- `calendar_audit_uncategorized` — scans next 14 days for uncolored events with suggestions
- `calendar_smart_schedule` — finds best slot before deadline, shows option, confirms before booking
- `calendar_confirm_smart_schedule` — books the pending smart schedule slot
- `calendar_conflict_report` — scans 30 days for overlaps and tight back-to-back events
- `calendar_weekly_prep` — weekly report of events needing attention, conflicts, uncategorized
- `get_day_of_week_date` — computes exact dates from relative day names using Python datetime

**Color Category Map:**
- 🔴 Tomato — Health / Medical
- 🟠 Tangerine — Social / Events
- 🟡 Banana — Errands / Personal
- 🟢 Basil — Fitness / Workout
- 🔵 Blueberry — Important / Work
- 🟣 Grape — Family
- ⚫ Graphite — Routine / Recurring
- 🩷 Flamingo — Birthdays / Anniversaries
- 🩵 Peacock — Travel / Trips

**Scheduler Files Created:**
- `calendar_audit_scheduler.py` — runs every 2 weeks, sends uncategorized event audit
- `weekly_prep_scheduler.py` — runs every Monday morning with weekly calendar prep report

**Issues Resolved:**
- Wrong date computation (Wednesday = April 9 not 8) — fixed with get_day_of_week_date
- Shared calendar events not showing — fixed with get_all_calendar_ids
- All-day events not showing — fixed datetime parsing
- Timezone offset showing previous night's events — fixed with Houston local timezone
- Recurring events treated as multiple different events — handled with recurringEventId detection
- Event intelligence auto-enriches new events with color, reminder, and location

---

### Phase 8: Habit Tracker ✅ COMPLETE

**Tools Built:**
- `habit_log` — logs a yes/no check-in for a habit with optional note
- `habit_view` — views habit history filtered by habit name and/or time period
- `habit_streak` — returns current streak and weekly summary for all three habits

**Habits Tracked:**
- 💪 workout
- 💧 water
- 🧘 stretching

**Implementation Details:**
- Entries stored in habits.txt: `[YYYY-MM-DD] habit: ✅/❌ — note`
- Display format reformatted to `Sat, 4.5.26 - habit: ✅` at view time (raw file unchanged)
- Natural language logging: "I worked out", "skipped my stretching", "drank water today"
- habit_scheduler.py sends daily check-in prompts via Telegram
- DISPLAY_RAW system implemented — habit log shown verbatim, never summarized by Claude

---

### Phase 9: Meal Planning ✅ COMPLETE

**Tools Built (via dedicated meal_agent.py):**
- `generate_meal_plan` — calls meal planning sub-agent, returns full weekly plan
- `view_meal_plan` — shows current saved meal plan
- `add_meal_groceries` — adds meal plan grocery items to grocery list with auto-categorization

**Implementation Details:**
- Dedicated second agent (meal_agent.py) handles all meal plan logic
- Meal preferences read from meal_preferences.txt
- Grocery items auto-categorized before adding to grocery list
- meal_scheduler.py prompts Mason every Sunday to generate a new plan
- DISPLAY_RAW system ensures full plan is always shown verbatim

---

### Phase 10: DISPLAY_RAW System ✅ COMPLETE

**Problem Solved:**
Claude was summarizing tool output instead of showing it verbatim — affecting habit logs, lists, grocery, meal plans, and calendar views.

**Implementation:**
- All display tools wrap output in `[DISPLAY_RAW]...[/DISPLAY_RAW]` tags
- Agent loop intercepts the tag before passing result to Claude
- Raw content sent directly to Telegram — Claude never sees the data
- Claude receives only `[Data displayed directly to Mason — X chars shown verbatim]`
- A lightweight follow-up call (max 200 tokens) allows Claude to add a brief one-liner if useful
- Any future tool that shows data just needs the tag — no system prompt changes needed

**Tools Covered (17 total):**
- habit_view, habit_streak
- list_view, list_show_all
- view_tasks
- get_todays_chores, get_maintenance_due
- calendar_get_today, calendar_get_events, calendar_bulk_view, calendar_find_free_time
- calendar_audit_uncategorized, calendar_conflict_report, calendar_weekly_prep
- generate_meal_plan, view_meal_plan

---

### Phase 11: Google Tasks Agent ✅ COMPLETE

**Tools Built (17 total via agents/tasks_agent.py):**

CRUD: `tasks_add`, `tasks_view`, `tasks_complete`, `tasks_delete`, `tasks_update`, `tasks_add_subtask`

List Management: `tasks_list_all`, `tasks_list_create`, `tasks_list_delete`, `tasks_list_rename`

Smart Views: `tasks_due_today`, `tasks_overdue`, `tasks_due_this_week`, `tasks_search`

Power Tools: `tasks_bulk_complete`, `tasks_weekly_summary`, `tasks_calendar_crosscheck`

**Implementation Details:**
- Standalone service module `agents/tasks_agent.py` — pure Google Tasks API, no Claude loop
- Shares OAuth token with Calendar via `core/google_auth.py` (single token.json, combined scopes)
- Priority tagging via [HIGH]/[MEDIUM]/[LOW] surfaced with 🔴/🟡/⚪ in all views
- Natural due date parsing via existing `get_day_of_week_date` tool
- DISPLAY_RAW applied to all view tools from day one
- `tasks_calendar_crosscheck` cross-references task due dates against Calendar busy days
- `tasks_scheduler.py` sends daily overdue/due-today nudge via Telegram
- Tool descriptions use explicit positive AND negative cases to prevent wrong tool selection

**Issues Resolved:**
- Claude calling `tasks_list_all` instead of `tasks_view` — fixed with precise tool descriptions specifying when NOT to use each tool
- Claude adding unnecessary follow-up commentary after list views — fixed by tightening DISPLAY_RAW follow-up prompt to default to silence

**Tests Passed:**
- ✅ tasks_view — showed all tasks in Main List verbatim
- ✅ tasks_add — added task with due date using natural day reference
- ✅ tasks_overdue — returned overdue tasks across all lists
- ✅ tasks_due_this_week — returned tasks grouped by day
- ✅ tasks_list_all — showed all lists with counts
- ✅ tasks_complete — marked task as done

---

### Phase 12: Agent Architecture Refactor ✅ COMPLETE

**New Folder Structure:**
```
my-first-agent/
├── agent.py                  — thin orchestrator: Telegram bot, agent loop, tool registry
├── agents/
│   ├── calendar_agent.py     — all Google Calendar functions
│   ├── tasks_agent.py        — all Google Tasks functions
│   ├── habits_agent.py       — habit tracking
│   ├── lists_agent.py        — smart list manager + grocery categorization
│   ├── chores_agent.py       — chores and home maintenance
│   ├── briefing_agent.py     — daily briefing and weather
│   └── meal_agent.py         — meal planning sub-agent
├── core/
│   ├── config.py             — all hardcoded values in one place
│   ├── google_auth.py        — single OAuth handler for all Google APIs
│   ├── display.py            — DISPLAY_RAW wrap_display() utility
│   └── telegram_utils.py     — shared Telegram send/chunking logic
├── tools/                    — reserved for future tool schema extraction
├── schedulers/               — all automated scheduler scripts
└── documents/                — all user data files
```

**Implementation Details:**
- `agent.py` reduced from 3400+ lines to ~600 lines — contains only orchestration logic
- Tool registry dict replaces 150-line if/elif chain — adding a new tool is one line
- `core/config.py` centralizes timezone, paths, habit names, list names, color maps, sports teams
- `core/google_auth.py` handles OAuth for all Google APIs — Calendar and Tasks share one token
- `core/display.py` provides `wrap_display()` — imported by every agent, tag format defined once
- All agents import from `core/` — no more hardcoded paths or scattered constants
- Schedulers moved to `schedulers/` subfolder with `sys.path` fix for imports
- Migration done incrementally — each agent extracted and syntax-checked before moving to next

**Tests Passed:**
- ✅ Full agent startup with new structure
- ✅ All existing tools functional after refactor
- ✅ Google Tasks integration working with shared OAuth
- ✅ DISPLAY_RAW system intact across all agents

---

---

## 📦 Archive — Deferred Phases

*These phases were scoped and planned but intentionally set aside. They can be revisited at any time.*

---

### ARCHIVED — Phase A: Learning Tracker + Capture Inbox + Weekly Reset

**Original Phase 8**

- Learning tracker — log AI/coding progress, track ideas, weekly Sunday summary
- Capture anything instantly — "remember this" saves to inbox file for later review
- Weekly reset routine — every Sunday evening: completed this week, coming next week, grocery list status, chore schedule preview

**Why Archived:**
Deprioritized in favor of higher-utility phases (Habit Tracker, Meal Planning, Google Tasks). Can be revisited when a more robust note-taking or journaling workflow is desired.

---

### ARCHIVED — Phase B: Proactive Reminder System

**Original Phase 11**

- Targeted reminders throughout the day beyond the morning briefing
- Chore reminders on assigned days (partially covered by chore_scheduler.py)
- Home maintenance alerts when due
- Weekly Sunday evening preview of the week ahead

**Why Archived:**
Core reminder functionality was absorbed into existing schedulers (briefing, chores, habits, meal). A more advanced proactive system can be built once the Google Workspace and architecture phases are complete, at which point it would integrate across Tasks, Calendar, and other services more meaningfully.

---

---

## 🗺 Action Plan — Phase 11 & 12

---

### Phase 11: Google Workspace Agent — Google Tasks

#### Overview

Google Tasks will be implemented as a **dedicated sub-agent** (`tasks_agent.py`), following the same pattern as `meal_agent.py`. It connects to the Google Tasks API using the same OAuth credentials already established for Google Calendar (shared `token.json` / `credentials.json` with an expanded scope).

The main `agent.py` exposes a set of `tasks_*` tools to Claude, which route internally to `tasks_agent.py` — keeping `agent.py` clean and all Tasks logic self-contained.

---

#### Core Tools to Build

**CRUD Basics:**
- `tasks_add` — add a task to a list with title, notes, and optional due date
- `tasks_view` — view all tasks in a list; filter by status (needsAction / completed) or due date
- `tasks_complete` — mark a task as complete
- `tasks_delete` — delete a task
- `tasks_update` — update title, notes, or due date on an existing task

**List Management:**
- `tasks_list_view_all` — show all task lists with item counts
- `tasks_list_create` — create a new task list
- `tasks_list_delete` — delete a task list

**Smart Features (matching Calendar depth):**
- `tasks_due_today` — returns all tasks due today across all lists
- `tasks_overdue` — returns all overdue tasks across all lists with how many days past due
- `tasks_due_this_week` — returns tasks due in the next 7 days grouped by day
- `tasks_search` — search for a task by keyword across all lists
- `tasks_bulk_complete` — mark multiple tasks complete at once ("clear my done items")
- `tasks_set_priority_order` — reorder tasks within a list by dragging priority (positional ordering via API)
- `tasks_add_subtask` — add a subtask (child task) under a parent task
- `tasks_calendar_sync_check` — cross-reference tasks with due dates against Calendar to flag conflicts or double-bookings

**Integration Features:**
- When adding a task with a due date, optionally offer to also block time on Calendar
- Tasks due today surface in the daily briefing alongside Calendar events
- Overdue tasks trigger a Telegram nudge via a new `tasks_scheduler.py`

---

#### Suggested Enhancements Beyond the Basics

- **Natural due date parsing** — "due next Friday", "due end of month" resolved via `get_day_of_week_date` (already built)
- **Priority labels** — tasks tagged [HIGH] / [MEDIUM] / [LOW] mirroring the existing task system, surfaced in views
- **DISPLAY_RAW on all view tools** — all task views follow the established pattern from Phase 10 from day one
- **Recurring tasks** — "add a weekly task to review my goals every Sunday"
- **tasks_weekly_summary** — Sunday scheduler report: what's due this week, what's overdue, what was completed last week

---

#### Files to Create/Modify

| File | Action |
|---|---|
| `tasks_agent.py` | New — all Google Tasks functions and API logic |
| `agent.py` | Add `tasks_*` tool definitions + route calls to tasks_agent |
| `tasks_scheduler.py` | New — daily overdue/due-today nudge via Telegram |
| `launch_agent.bat` | No changes needed (OAuth reuses existing credentials) |
| `Personal_Agent_-_Step_by_Step.md` | Update after completion |

---

#### OAuth Scope Addition Required

The existing `credentials.json` will need `https://www.googleapis.com/auth/tasks` added to the SCOPES list and `token.json` deleted once so it re-authenticates with the new scope. This is a one-time step.

---

### Phase 12: Agent Architecture Refactor

#### The Problem

Right now everything lives in `agent.py`. As more Google services, agents, and schedulers get added, this becomes hard to maintain, debug, and extend. The architecture needs a structure that scales.

---

#### Recommended Structure

```
my-first-agent/
│
├── agent.py                  # Main orchestrator — Telegram bot, agent loop, tool router
│
├── agents/                   # All sub-agents (one file per service/domain)
│   ├── calendar_agent.py     # All Google Calendar functions (extracted from agent.py)
│   ├── tasks_agent.py        # Google Tasks (new — Phase 11)
│   ├── meal_agent.py         # Meal planning (already standalone — move here)
│   ├── briefing_agent.py     # Daily briefing logic (extracted from agent.py)
│   └── lists_agent.py        # Smart list manager (extracted from agent.py)
│
├── tools/                    # Tool definitions (the JSON schema dicts Claude sees)
│   ├── calendar_tools.py     # Tool definitions for calendar
│   ├── tasks_tools.py        # Tool definitions for tasks
│   ├── lists_tools.py        # Tool definitions for lists
│   └── core_tools.py         # Search, calculator, file, date tools
│
├── schedulers/               # All automated scheduler scripts
│   ├── briefing_scheduler.py
│   ├── chore_scheduler.py
│   ├── habit_scheduler.py
│   ├── meal_scheduler.py
│   ├── tasks_scheduler.py    # New — Phase 11
│   ├── weekly_prep_scheduler.py
│   ├── calendar_audit_scheduler.py
│   └── weekly_reset_scheduler.py
│
├── documents/                # All user data files (lists, habits, tasks, etc.)
├── credentials.json          # Google OAuth credentials
├── token.json                # Google OAuth token
├── meal_preferences.txt      # Meal planning preferences
└── launch_agent.bat          # Launch script
```

---

#### Why This Structure

- **`agents/`** — each Google service or domain has its own file. Adding Gmail, Drive, or Keep later means creating one new file, not modifying `agent.py`
- **`tools/`** — separating tool definitions from logic means Claude's tool list can be assembled modularly. New tools from any agent are just imported and merged
- **`schedulers/`** — all scheduled scripts in one place, easy to manage in Task Scheduler
- **`agent.py` stays thin** — it imports from agents and tools, runs the loop, handles Telegram. It never gets bloated again

---

#### Migration Approach

Rather than rewriting everything at once, the refactor happens incrementally:
1. Create the folder structure
2. Extract `calendar_agent.py` first (largest, most self-contained)
3. Extract `lists_agent.py` and `briefing_agent.py`
4. Move `meal_agent.py` into `agents/`
5. Move `schedulers/` files
6. Split tool definitions into `tools/`
7. Update `agent.py` imports
8. Test each extraction before moving to the next

---

#### Additional Enhancements to Consider

**Across both phases:**
- **Shared Google auth module** (`google_auth.py`) — one function that returns an authenticated service for any Google API. Calendar, Tasks, and future services (Gmail, Drive) all call the same helper instead of each managing their own OAuth flow
- **Central config file** (`config.py`) — timezone, team names for briefing, habit list, list names, scheduler times — all in one place instead of scattered as hardcoded strings
- **Agent health check** — a `/status` command in Telegram that reports: agent running, last briefing sent, tasks overdue count, habits logged today. Good for debugging without opening the terminal
- **Error logging to file** — currently errors just print to console. A simple `errors.log` file that captures exceptions with timestamps means you can diagnose issues that happened while you weren't watching the terminal
- **Unified `run_tool` registry** — instead of a massive if/elif chain, use a Python dict that maps tool names to functions. Adding a new tool is one line. This scales cleanly with the modular architecture

---