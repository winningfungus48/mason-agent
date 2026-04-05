"""
agents/briefing_agent.py
------------------------
Daily briefing and weather functions for Mason's Personal Agent.
"""

import os
from datetime import date
from tavily import TavilyClient
from core.config import DOCUMENTS_DIR, SPORTS_TEAMS, CITY_NEWS_QUERY


def get_weather():
    try:
        print("  [TOOL] Getting Houston weather")
        if not os.getenv("TAVILY_API_KEY"):
            return "Error: TAVILY_API_KEY is not set."
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = tavily.search(
            query="Houston TX weather forecast today",
            max_results=3,
            search_depth="advanced"
        )
        if not results or not results.get("results"):
            return "Could not retrieve weather data."
        return "\n".join(f"- {r['title']}: {r['content']}" for r in results["results"])
    except Exception as e:
        return f"Weather error: {str(e)}"


def get_daily_briefing():
    try:
        print("  [TOOL] Generating daily briefing")
        today = date.today().strftime("%A, %B %d, %Y")
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        def search(query, max_results=5, topic=None, days=1):
            kwargs = dict(query=query, max_results=max_results, search_depth="advanced")
            if topic:
                kwargs["topic"] = topic
                kwargs["days"] = days
            results = tavily.search(**kwargs)
            return "\n".join(
                f"- {r['title']}: {r['content']}"
                for r in results.get("results", [])
            ) or "No results available."

        weather      = search("Houston TX weather forecast today", max_results=2)
        breaking     = search("breaking news major world events today", topic="news", days=1)
        world_news   = search("top world news today", topic="news", days=1)
        houston_news = search("Houston Texas local news today", topic="news", days=1)
        city_news    = search(CITY_NEWS_QUERY, topic="news", days=1)
        tech_news    = search("technology news today", topic="news", days=1)
        ai_companies = search(
            "AI company product launch feature announcement today OpenAI Anthropic Google Meta Microsoft",
            topic="news", days=1
        )
        ai_tip       = search("practical AI productivity tip for everyday use", max_results=2)
        sports       = search(
            f"{SPORTS_TEAMS.replace(' | ', ' ')} latest news today",
            topic="news", days=1
        )
        week_glance  = search(
            f"upcoming events holidays deadlines this week {date.today().strftime('%B %Y')}",
            max_results=3
        )

        # Pending local tasks
        tasks_filepath = os.path.join(DOCUMENTS_DIR, "tasks.txt")
        if os.path.exists(tasks_filepath):
            with open(tasks_filepath, "r", encoding="utf-8") as f:
                all_tasks = [l.strip() for l in f.readlines() if l.strip()]
            pending = [t for t in all_tasks if "status:pending" in t]
            pending.sort(key=lambda l: 0 if "priority:high" in l else 1 if "priority:medium" in l else 2)
            tasks_summary = "\n".join(f"- {t}" for t in pending) if pending else "No pending tasks."
        else:
            tasks_summary = "No task list found."

        # Today's calendar (imported here to avoid circular import)
        try:
            from agents.calendar_agent import calendar_get_today
            calendar_today = calendar_get_today()
            # Strip DISPLAY_RAW tags for embedding in briefing
            if "[DISPLAY_RAW]" in calendar_today:
                calendar_today = calendar_today.split("[DISPLAY_RAW]")[1].split("[/DISPLAY_RAW]")[0].strip()
        except Exception:
            calendar_today = "Calendar unavailable."

        return f"""
DATE: {today}

WEATHER (Houston, TX):
{weather}

TODAYS CALENDAR:
{calendar_today}

BREAKING / MAJOR NEWS:
{breaking}

WORLD NEWS:
{world_news}

HOUSTON LOCAL NEWS:
{houston_news}

CITY NEWS (College Station / Canyon Lake / Milwaukee / Fort Worth):
{city_news}

TECH & GENERAL AI NEWS:
{tech_news}

AI COMPANIES & PRODUCT NEWS (new launches, features, announcements):
{ai_companies}

AI TIP OF THE DAY:
{ai_tip}

SPORTS NEWS:
Teams: {SPORTS_TEAMS}
{sports}

THIS WEEK AT A GLANCE:
{week_glance}

PENDING TASKS:
{tasks_summary}
"""
    except Exception as e:
        return f"Briefing error: {str(e)}"
