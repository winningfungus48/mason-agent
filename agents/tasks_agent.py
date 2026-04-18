"""
tasks_agent.py
--------------
Google Tasks service module for Mason's Personal Agent.
Called by agent.py tool router — no Claude loop here, pure API functions.
Shares OAuth credentials with Google Calendar (token.json / credentials.json).
Requires scope: https://www.googleapis.com/auth/tasks
"""

import os
import datetime
from core.google_auth import get_service
from core.display import wrap_display as _wrap_display

def get_tasks_service():
    """Return authenticated Google Tasks service via shared auth."""
    return get_service("tasks", "v1")


def wrap_display(content):
    """Wrap content in DISPLAY_RAW tags so agent loop sends it verbatim to Telegram."""
    return _wrap_display(content)


def get_all_task_lists(service):
    """Return all task lists as list of (id, title) tuples."""
    result = service.tasklists().list(maxResults=100).execute()
    return [(tl['id'], tl['title']) for tl in result.get('items', [])]


def find_list_by_name(service, list_name):
    """Fuzzy match a task list by name. Returns (list_id, list_title) or (None, None)."""
    all_lists = get_all_task_lists(service)
    name_lower = list_name.lower().strip()
    # Exact match first
    for lid, title in all_lists:
        if title.lower() == name_lower:
            return lid, title
    # Partial match
    for lid, title in all_lists:
        if name_lower in title.lower() or title.lower() in name_lower:
            return lid, title
    return None, None


def parse_due_date(due_str):
    """
    Convert a due date string (YYYY-MM-DD) to RFC3339 format required by Tasks API.
    Returns None if due_str is None or empty.
    """
    if not due_str:
        return None
    try:
        dt = datetime.datetime.strptime(due_str, '%Y-%m-%d')
        # Tasks API requires RFC3339 with time set to midnight UTC
        return dt.strftime('%Y-%m-%dT00:00:00.000Z')
    except Exception:
        return None


def format_due_date(due_str):
    """Format an RFC3339 due date string for display. Returns '' if None."""
    if not due_str:
        return ''
    try:
        dt = datetime.datetime.strptime(due_str[:10], '%Y-%m-%d')
        return dt.strftime('%a, %-m.%-d.%y')
    except Exception:
        try:
            dt = datetime.datetime.strptime(due_str[:10], '%Y-%m-%d')
            return dt.strftime('%a, %#m.%#d.%y')  # Windows fallback
        except Exception:
            return due_str[:10]


def is_overdue(due_str):
    """Return True if the due date is before today."""
    if not due_str:
        return False
    try:
        due = datetime.datetime.strptime(due_str[:10], '%Y-%m-%d').date()
        return due < datetime.date.today()
    except Exception:
        return False


def days_overdue(due_str):
    """Return number of days a task is overdue. 0 if not overdue."""
    if not due_str:
        return 0
    try:
        due = datetime.datetime.strptime(due_str[:10], '%Y-%m-%d').date()
        delta = (datetime.date.today() - due).days
        return max(0, delta)
    except Exception:
        return 0


# ─────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────

def tasks_add(title, list_name=None, notes=None, due_date=None, priority=None):
    """Add a task to a task list."""
    try:
        print(f"  [TOOL] Adding task: {title}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            if not list_id:
                return f"Could not find a task list named '{list_name}'."
        else:
            # Default to first list (usually 'My Tasks')
            all_lists = get_all_task_lists(service)
            if not all_lists:
                return "No task lists found in Google Tasks."
            list_id, list_display = all_lists[0]

        body = {'title': title}
        if notes:
            body['notes'] = notes
        if due_date:
            rfc_due = parse_due_date(due_date)
            if rfc_due:
                body['due'] = rfc_due
        if priority:
            # Store priority in notes prefix since Tasks API has no priority field
            priority_tag = f"[{priority.upper()}] "
            body['notes'] = priority_tag + (notes or '')

        service.tasks().insert(tasklist=list_id, body=body).execute()

        due_label = f" | due {format_due_date(due_date)}" if due_date else ""
        pri_label = f" | [{priority.upper()}]" if priority else ""
        return f"✅ Added to '{list_display}': {title}{pri_label}{due_label}"
    except Exception as e:
        return f"Error adding task: {str(e)}"


def tasks_view(list_name=None, status_filter='needsAction', due_filter=None):
    """
    View tasks in a list. status_filter: 'needsAction', 'completed', or 'all'.
    due_filter: 'today', 'this_week', or None for all.
    """
    try:
        print(f"  [TOOL] Viewing tasks in: {list_name or 'all lists'}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            if not list_id:
                return f"Could not find a task list named '{list_name}'."
            lists_to_check = [(list_id, list_display)]
        else:
            lists_to_check = get_all_task_lists(service)

        today = datetime.date.today()
        week_end = today + datetime.timedelta(days=7)
        all_output = []

        for list_id, list_display in lists_to_check:
            kwargs = {'tasklist': list_id, 'maxResults': 100, 'showCompleted': True}
            if status_filter == 'needsAction':
                kwargs['showCompleted'] = False
            result = service.tasks().list(**kwargs).execute()
            items = result.get('items', [])

            # Filter by status
            if status_filter == 'needsAction':
                items = [t for t in items if t.get('status') == 'needsAction']
            elif status_filter == 'completed':
                items = [t for t in items if t.get('status') == 'completed']

            # Filter by due date
            if due_filter == 'today':
                items = [t for t in items if t.get('due', '')[:10] == today.strftime('%Y-%m-%d')]
            elif due_filter == 'this_week':
                items = [t for t in items if t.get('due') and
                         today.strftime('%Y-%m-%d') <= t['due'][:10] <= week_end.strftime('%Y-%m-%d')]

            if not items:
                continue

            block = f"📋 {list_display.upper()}:\n"
            for t in items:
                title = t.get('title', '(no title)')
                due = t.get('due', '')
                notes = t.get('notes', '')
                status_icon = '✅' if t.get('status') == 'completed' else '•'
                due_label = f" — due {format_due_date(due)}" if due else ""
                overdue_label = " ⚠️ OVERDUE" if is_overdue(due) and t.get('status') != 'completed' else ""
                notes_label = f"\n    📝 {notes}" if notes and not notes.startswith('[') else ""
                # Surface priority from notes prefix
                pri_label = ""
                if notes and notes.startswith('[HIGH]'):
                    pri_label = " 🔴"
                elif notes and notes.startswith('[MEDIUM]'):
                    pri_label = " 🟡"
                elif notes and notes.startswith('[LOW]'):
                    pri_label = " ⚪"
                block += f"  {status_icon} {title}{pri_label}{due_label}{overdue_label}{notes_label}\n"
            all_output.append(block)

        if not all_output:
            filter_label = f" matching '{due_filter}'" if due_filter else ""
            return f"No tasks found{filter_label}."

        content = "\n".join(all_output).strip()
        return wrap_display(content)
    except Exception as e:
        return f"Error viewing tasks: {str(e)}"


def tasks_complete(title_search, list_name=None):
    """Mark a task as complete by searching for its title."""
    try:
        print(f"  [TOOL] Completing task: {title_search}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
            for task in result.get('items', []):
                if title_search.lower() in task.get('title', '').lower():
                    # Use patch() with only the fields being changed + completed timestamp
                    # update() with a list-fetched body silently fails due to missing fields
                    completed_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    service.tasks().patch(
                        tasklist=list_id,
                        task=task['id'],
                        body={'status': 'completed', 'completed': completed_time}
                    ).execute()
                    return f"✅ Marked complete: '{task['title']}' in '{list_display}'"

        return f"No pending task matching '{title_search}' was found."
    except Exception as e:
        return f"Error completing task: {str(e)}"


def tasks_reopen(title_search, list_name=None):
    """Mark a completed task as needsAction again (same list scope as tasks_complete)."""
    try:
        print(f"  [TOOL] Reopening task: {title_search}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=True).execute()
            for task in result.get('items', []):
                if task.get('status') != 'completed':
                    continue
                if title_search.lower() in task.get('title', '').lower():
                    service.tasks().patch(
                        tasklist=list_id,
                        task=task['id'],
                        body={'status': 'needsAction'},
                    ).execute()
                    return f"✅ Reopened: '{task['title']}' in '{list_display}'"

        return f"No completed task matching '{title_search}' was found."
    except Exception as e:
        return f"Error reopening task: {str(e)}"


def tasks_delete(title_search, list_name=None):
    """Delete a task by searching for its title."""
    try:
        print(f"  [TOOL] Deleting task: {title_search}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=True).execute()
            for task in result.get('items', []):
                if title_search.lower() in task.get('title', '').lower():
                    service.tasks().delete(tasklist=list_id, task=task['id']).execute()
                    return f"🗑️ Deleted '{task['title']}' from '{list_display}'"

        return f"No task matching '{title_search}' was found."
    except Exception as e:
        return f"Error deleting task: {str(e)}"


def tasks_update(title_search, new_title=None, new_notes=None, new_due_date=None,
                 new_priority=None, list_name=None):
    """Update a task's title, notes, due date, or priority."""
    try:
        print(f"  [TOOL] Updating task: {title_search}")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(tasklist=list_id, maxResults=100, showCompleted=False).execute()
            for task in result.get('items', []):
                if title_search.lower() in task.get('title', '').lower():
                    if new_title:
                        task['title'] = new_title
                    if new_due_date:
                        rfc_due = parse_due_date(new_due_date)
                        if rfc_due:
                            task['due'] = rfc_due
                    if new_priority:
                        existing_notes = task.get('notes', '')
                        # Remove existing priority tag if present
                        import re
                        existing_notes = re.sub(r'^\[(HIGH|MEDIUM|LOW)\]\s*', '', existing_notes)
                        task['notes'] = f"[{new_priority.upper()}] {existing_notes}".strip()
                    elif new_notes is not None:
                        task['notes'] = new_notes

                    service.tasks().update(
                        tasklist=list_id, task=task['id'], body=task
                    ).execute()

                    changes = []
                    if new_title: changes.append(f"title → '{new_title}'")
                    if new_due_date: changes.append(f"due → {format_due_date(new_due_date)}")
                    if new_priority: changes.append(f"priority → {new_priority.upper()}")
                    if new_notes: changes.append("notes updated")
                    return f"✅ Updated '{task['title']}': {', '.join(changes)}"

        return f"No pending task matching '{title_search}' was found."
    except Exception as e:
        return f"Error updating task: {str(e)}"


def tasks_add_subtask(parent_title, subtask_title, list_name=None):
    """Add a subtask (child) under an existing parent task."""
    try:
        print(f"  [TOOL] Adding subtask '{subtask_title}' under '{parent_title}'")
        service = get_tasks_service()

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(tasklist=list_id, maxResults=100).execute()
            for task in result.get('items', []):
                if parent_title.lower() in task.get('title', '').lower():
                    body = {'title': subtask_title}
                    service.tasks().insert(
                        tasklist=list_id, body=body, parent=task['id']
                    ).execute()
                    return f"✅ Added subtask '{subtask_title}' under '{task['title']}'"

        return f"No task matching '{parent_title}' was found."
    except Exception as e:
        return f"Error adding subtask: {str(e)}"


# ─────────────────────────────────────────────
# LIST MANAGEMENT
# ─────────────────────────────────────────────

def tasks_list_all():
    """Show all task lists with pending item counts."""
    try:
        print(f"  [TOOL] Listing all task lists")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)

        if not all_lists:
            return "No task lists found."

        content = "📋 GOOGLE TASK LISTS:\n\n"
        for list_id, title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            pending = [t for t in result.get('items', []) if t.get('status') == 'needsAction']
            overdue = [t for t in pending if is_overdue(t.get('due', ''))]
            overdue_label = f" ⚠️ {len(overdue)} overdue" if overdue else ""
            content += f"• {title}: {len(pending)} pending{overdue_label}\n"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error listing task lists: {str(e)}"


def tasks_list_create(list_name):
    """Create a new task list."""
    try:
        print(f"  [TOOL] Creating task list: {list_name}")
        service = get_tasks_service()
        result = service.tasklists().insert(body={'title': list_name}).execute()
        return f"✅ Created new task list: '{result['title']}'"
    except Exception as e:
        return f"Error creating task list: {str(e)}"


def tasks_list_delete(list_name):
    """Delete a task list."""
    try:
        print(f"  [TOOL] Deleting task list: {list_name}")
        service = get_tasks_service()
        list_id, list_display = find_list_by_name(service, list_name)
        if not list_id:
            return f"Could not find a task list named '{list_name}'."
        service.tasklists().delete(tasklist=list_id).execute()
        return f"🗑️ Deleted task list: '{list_display}'"
    except Exception as e:
        return f"Error deleting task list: {str(e)}"


def tasks_list_rename(old_name, new_name):
    """Rename an existing task list."""
    try:
        print(f"  [TOOL] Renaming task list: {old_name} → {new_name}")
        service = get_tasks_service()
        list_id, list_display = find_list_by_name(service, old_name)
        if not list_id:
            return f"Could not find a task list named '{old_name}'."
        service.tasklists().patch(tasklist=list_id, body={'title': new_name}).execute()
        return f"✅ Renamed '{list_display}' → '{new_name}'"
    except Exception as e:
        return f"Error renaming task list: {str(e)}"


# ─────────────────────────────────────────────
# SMART VIEWS
# ─────────────────────────────────────────────

def tasks_due_today():
    """Return all tasks due today across all lists."""
    try:
        print(f"  [TOOL] Getting tasks due today")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        today_fmt = datetime.date.today().strftime('%A, %B %-d')

        found = []
        for list_id, list_title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for t in result.get('items', []):
                if t.get('due', '')[:10] == today_str and t.get('status') == 'needsAction':
                    found.append((list_title, t.get('title', '(no title)'), t.get('notes', '')))

        if not found:
            return f"No tasks due today ({today_fmt}) 🎉"

        content = f"📅 TASKS DUE TODAY ({today_fmt}):\n\n"
        for list_title, title, notes in found:
            pri = ""
            if notes.startswith('[HIGH]'): pri = " 🔴"
            elif notes.startswith('[MEDIUM]'): pri = " 🟡"
            content += f"• {title}{pri} [{list_title}]\n"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error getting today's tasks: {str(e)}"


def tasks_overdue():
    """Return all overdue tasks across all lists sorted by how late they are."""
    try:
        print(f"  [TOOL] Getting overdue tasks")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)

        found = []
        for list_id, list_title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for t in result.get('items', []):
                due = t.get('due', '')
                if is_overdue(due) and t.get('status') == 'needsAction':
                    found.append((
                        days_overdue(due),
                        list_title,
                        t.get('title', '(no title)'),
                        t.get('notes', ''),
                        due
                    ))

        if not found:
            return "✅ No overdue tasks!"

        found.sort(reverse=True)  # Most overdue first
        content = f"⚠️ OVERDUE TASKS ({len(found)} total):\n\n"
        for days, list_title, title, notes, due in found:
            pri = ""
            if notes.startswith('[HIGH]'): pri = " 🔴"
            elif notes.startswith('[MEDIUM]'): pri = " 🟡"
            day_label = f"{days} day{'s' if days != 1 else ''} overdue"
            content += f"• {title}{pri} — {day_label} [{list_title}]\n"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error getting overdue tasks: {str(e)}"


def tasks_due_this_week():
    """Return tasks due in the next 7 days grouped by day."""
    try:
        print(f"  [TOOL] Getting tasks due this week")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)

        today = datetime.date.today()
        week_end = today + datetime.timedelta(days=7)

        from collections import defaultdict
        by_day = defaultdict(list)

        for list_id, list_title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for t in result.get('items', []):
                due = t.get('due', '')
                if not due:
                    continue
                due_date = due[:10]
                if today.strftime('%Y-%m-%d') <= due_date <= week_end.strftime('%Y-%m-%d'):
                    if t.get('status') == 'needsAction':
                        by_day[due_date].append((list_title, t.get('title', '(no title)'), t.get('notes', '')))

        if not by_day:
            return "No tasks due in the next 7 days 🎉"

        content = "📅 TASKS DUE THIS WEEK:\n"
        for day_str in sorted(by_day.keys()):
            day_dt = datetime.datetime.strptime(day_str, '%Y-%m-%d').date()
            label = "Today" if day_dt == today else "Tomorrow" if day_dt == today + datetime.timedelta(days=1) else day_dt.strftime('%A, %b %-d')
            content += f"\n{label}:\n"
            for list_title, title, notes in by_day[day_str]:
                pri = ""
                if notes.startswith('[HIGH]'): pri = " 🔴"
                elif notes.startswith('[MEDIUM]'): pri = " 🟡"
                content += f"  • {title}{pri} [{list_title}]\n"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error getting this week's tasks: {str(e)}"


def tasks_search(keyword):
    """Search for tasks by keyword across all lists."""
    try:
        print(f"  [TOOL] Searching tasks for: {keyword}")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)
        kw = keyword.lower()

        found = []
        for list_id, list_title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=True
            ).execute()
            for t in result.get('items', []):
                title = t.get('title', '')
                notes = t.get('notes', '')
                if kw in title.lower() or kw in notes.lower():
                    status_icon = '✅' if t.get('status') == 'completed' else '•'
                    due = t.get('due', '')
                    due_label = f" — due {format_due_date(due)}" if due else ""
                    found.append(f"  {status_icon} {title}{due_label} [{list_title}]")

        if not found:
            return f"No tasks found matching '{keyword}'."

        content = f"🔍 SEARCH RESULTS FOR '{keyword}':\n\n" + "\n".join(found)
        return wrap_display(content.strip())
    except Exception as e:
        return f"Error searching tasks: {str(e)}"


def tasks_bulk_complete(title_list, list_name=None):
    """
    Mark multiple tasks complete at once.
    title_list: comma-separated string of task titles to complete.
    """
    try:
        print(f"  [TOOL] Bulk completing tasks")
        service = get_tasks_service()
        titles = [t.strip() for t in title_list.split(',') if t.strip()]

        if list_name:
            list_id, list_display = find_list_by_name(service, list_name)
            lists_to_check = [(list_id, list_display)] if list_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        completed = []
        not_found = list(titles)

        for list_id, list_display in lists_to_check:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for task in result.get('items', []):
                task_title = task.get('title', '')
                for search_title in list(not_found):
                    if search_title.lower() in task_title.lower():
                        completed_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
                        service.tasks().patch(
                            tasklist=list_id,
                            task=task['id'],
                            body={'status': 'completed', 'completed': completed_time}
                        ).execute()
                        completed.append(task_title)
                        not_found.remove(search_title)
                        break

        lines = [f"✅ {t}" for t in completed]
        if not_found:
            lines += [f"❓ Not found: {t}" for t in not_found]
        return "\n".join(lines) if lines else "No tasks matched."
    except Exception as e:
        return f"Error bulk completing tasks: {str(e)}"


def tasks_weekly_summary():
    """
    Summary: due this week, overdue, completed last week.
    Used by tasks_scheduler.py and on-demand.
    """
    try:
        print(f"  [TOOL] Generating tasks weekly summary")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)

        today = datetime.date.today()
        week_end = today + datetime.timedelta(days=7)
        last_week_start = today - datetime.timedelta(days=7)

        due_this_week = []
        overdue_tasks = []
        completed_last_week = []

        for list_id, list_title in all_lists:
            # Pending tasks
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for t in result.get('items', []):
                due = t.get('due', '')
                title = t.get('title', '(no title)')
                if is_overdue(due):
                    overdue_tasks.append((days_overdue(due), title, list_title))
                elif due and today.strftime('%Y-%m-%d') <= due[:10] <= week_end.strftime('%Y-%m-%d'):
                    day_dt = datetime.datetime.strptime(due[:10], '%Y-%m-%d').date()
                    due_this_week.append((day_dt, title, list_title))

            # Completed last week
            result_done = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=True
            ).execute()
            for t in result_done.get('items', []):
                if t.get('status') == 'completed':
                    completed = t.get('completed', '')
                    if completed and completed[:10] >= last_week_start.strftime('%Y-%m-%d'):
                        completed_last_week.append((t.get('title', '(no title)'), list_title))

        content = f"📊 TASKS WEEKLY SUMMARY\n"
        content += f"Week of {today.strftime('%B %-d')}:\n\n"

        if overdue_tasks:
            overdue_tasks.sort(reverse=True)
            content += f"⚠️ OVERDUE ({len(overdue_tasks)}):\n"
            for days, title, list_title in overdue_tasks[:10]:
                content += f"  • {title} — {days}d overdue [{list_title}]\n"
            content += "\n"

        if due_this_week:
            due_this_week.sort()
            content += f"📅 DUE THIS WEEK ({len(due_this_week)}):\n"
            for day_dt, title, list_title in due_this_week:
                day_label = "Today" if day_dt == today else day_dt.strftime('%a %-d')
                content += f"  • {title} — {day_label} [{list_title}]\n"
            content += "\n"

        if completed_last_week:
            content += f"✅ COMPLETED LAST WEEK ({len(completed_last_week)}):\n"
            for title, list_title in completed_last_week[:10]:
                content += f"  • {title} [{list_title}]\n"

        if not overdue_tasks and not due_this_week and not completed_last_week:
            content += "Nothing due or overdue. Clean slate! 🎉"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error generating weekly summary: {str(e)}"


def tasks_calendar_crosscheck():
    """
    Cross-reference tasks that have due dates against Calendar to surface
    tasks due on days that are already fully booked (no free time blocks).
    Requires calendar service — imported here to avoid circular import.
    """
    try:
        print(f"  [TOOL] Cross-checking tasks against calendar")
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        from core.config import TOKEN_PATH; token_path = TOKEN_PATH
        cal_scopes = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/tasks']
        cal_creds = Credentials.from_authorized_user_file(token_path, cal_scopes)
        cal_service = build('calendar', 'v3', credentials=cal_creds)

        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        tasks_service = get_tasks_service()
        all_lists = get_all_task_lists(tasks_service)

        today = datetime.date.today()
        week_end = today + datetime.timedelta(days=7)

        # Collect task due dates
        task_due_days = {}  # date_str -> list of task titles
        for list_id, list_title in all_lists:
            result = tasks_service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for t in result.get('items', []):
                due = t.get('due', '')
                if due and today.strftime('%Y-%m-%d') <= due[:10] <= week_end.strftime('%Y-%m-%d'):
                    task_due_days.setdefault(due[:10], []).append(t.get('title', '(no title)'))

        if not task_due_days:
            return "No tasks with due dates this week to cross-check."

        # Check calendar busyness for each due date
        warnings = []
        for day_str, task_titles in sorted(task_due_days.items()):
            day_dt = datetime.datetime.strptime(day_str, '%Y-%m-%d')
            time_min = datetime.datetime(day_dt.year, day_dt.month, day_dt.day, 8, 0,
                                         tzinfo=houston_tz).isoformat()
            time_max = datetime.datetime(day_dt.year, day_dt.month, day_dt.day, 21, 0,
                                         tzinfo=houston_tz).isoformat()

            cal_result = cal_service.events().list(
                calendarId='primary',
                timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy='startTime'
            ).execute()

            events = cal_result.get('items', [])
            timed_events = [e for e in events if 'dateTime' in e.get('start', {})]
            busy_hours = sum(
                (datetime.datetime.fromisoformat(e['end']['dateTime'][:19]) -
                 datetime.datetime.fromisoformat(e['start']['dateTime'][:19])).seconds / 3600
                for e in timed_events
            )

            day_label = datetime.datetime.strptime(day_str, '%Y-%m-%d').strftime('%A, %b %-d')
            if busy_hours >= 6:
                for title in task_titles:
                    warnings.append(f"  ⚠️ '{title}' due {day_label} — calendar is very busy ({busy_hours:.0f}h booked)")
            elif timed_events:
                for title in task_titles:
                    warnings.append(f"  • '{title}' due {day_label} — {len(timed_events)} event(s) that day")

        if not warnings:
            return "✅ No scheduling conflicts found between tasks and calendar this week."

        content = "📅 TASK vs CALENDAR CROSSCHECK:\n\n" + "\n".join(warnings)
        return wrap_display(content.strip())
    except Exception as e:
        return f"Error running crosscheck: {str(e)}"


# ─────────────────────────────────────────────
# PHASE 13C — ORGANIZATION & ENHANCEMENTS
# ─────────────────────────────────────────────

# Life-area list definitions
LIFE_AREA_LISTS = {
    "🏠 Home":              "Home maintenance, repairs, household purchases, improvements",
    "🚗 Errands & Auto":    "Oil change, DMV, returns, appointments to book, car-related tasks",
    "💰 Finance":           "Budget, bills, insurance, investments, financial to-dos",
    "🛒 Grocery & Essentials": "One-off grocery items and household essentials that come to mind mid-week",
    "🛍️ Buy List":          "Personal purchases, gear, clothing, things to order online",
    "💪 Health & Fitness":  "Doctor appointments, fitness goals, supplements, health-related tasks",
    "🤖 AI & Learning":     "AI projects, things to try, research, learning goals",
}

# Keyword → list name mapping for smart categorization
LIST_CATEGORY_KEYWORDS = {
    "🏠 Home": [
        "fix", "repair", "replace", "install", "clean", "paint", "garage",
        "lawn", "yard", "fence", "roof", "gutter", "plumber", "electrician",
        "furniture", "appliance", "hvac", "filter", "vacuum", "mop",
    ],
    "🚗 Errands & Auto": [
        "oil change", "car", "tire", "registration", "dmv", "license",
        "errand", "pick up", "drop off", "return", "post office", "bank",
        "dry clean", "pharmacy", "prescription", "appointment",
    ],
    "💰 Finance": [
        "budget", "bill", "pay", "insurance", "invest", "tax", "401k",
        "savings", "credit card", "loan", "rent", "mortgage", "expense",
        "financial", "bank", "transfer", "subscription",
    ],
    "🛒 Grocery & Essentials": [
        "buy", "grocery", "milk", "eggs", "bread", "food", "drink",
        "paper towel", "toilet paper", "soap", "detergent", "household",
        "stock up", "restock",
    ],
    "🛍️ Buy List": [
        "order", "purchase", "amazon", "shoes", "clothes", "shirt",
        "pants", "headphones", "phone", "laptop", "gadget", "gear",
        "equipment", "gift", "present",
    ],
    "💪 Health & Fitness": [
        "doctor", "dentist", "gym", "workout", "run", "exercise",
        "vitamin", "supplement", "therapy", "physical", "checkup",
        "health", "medical", "weight", "diet", "sleep",
    ],
    "🤖 AI & Learning": [
        "learn", "study", "read", "research", "ai", "claude", "gpt",
        "course", "tutorial", "practice", "code", "build", "project",
        "experiment", "explore",
    ],
}


def guess_task_list(title):
    """
    Suggest a life-area list based on task title keywords.
    Returns list name string or None if no match.
    """
    title_lower = title.lower()
    for list_name, keywords in LIST_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return list_name
    return None


def tasks_setup_lists():
    """
    Create all 7 life-area task lists in Google Tasks.
    Skips lists that already exist. Safe to run multiple times.
    """
    try:
        print("  [TOOL] Setting up life-area task lists")
        service = get_tasks_service()
        existing = get_all_task_lists(service)
        existing_names = [title for _, title in existing]

        created = []
        skipped = []

        for list_name in LIFE_AREA_LISTS:
            if list_name in existing_names:
                skipped.append(list_name)
            else:
                service.tasklists().insert(body={'title': list_name}).execute()
                created.append(list_name)

        result = "✅ TASK LISTS SETUP COMPLETE:\n\n"
        if created:
            result += "Created:\n" + "\n".join(f"• {n}" for n in created) + "\n\n"
        if skipped:
            result += "Already existed (skipped):\n" + "\n".join(f"• {n}" for n in skipped)

        return result.strip()
    except Exception as e:
        return f"Error setting up lists: {str(e)}"


def tasks_move(title_search, target_list, source_list=None):
    """
    Move a task from one list to another.
    Finds the task, creates it in the target list, deletes from source.
    """
    try:
        print(f"  [TOOL] Moving task '{title_search}' to '{target_list}'")
        service = get_tasks_service()

        # Find target list
        target_id, target_display = find_list_by_name(service, target_list)
        if not target_id:
            return f"Could not find target list '{target_list}'."

        # Search source lists
        if source_list:
            source_id, source_display = find_list_by_name(service, source_list)
            lists_to_check = [(source_id, source_display)] if source_id else []
        else:
            lists_to_check = get_all_task_lists(service)

        for list_id, list_display in lists_to_check:
            if list_id == target_id:
                continue
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            for task in result.get('items', []):
                if title_search.lower() in task.get('title', '').lower():
                    # Create in target list
                    new_body = {
                        'title': task.get('title', ''),
                        'notes': task.get('notes', ''),
                    }
                    if task.get('due'):
                        new_body['due'] = task['due']

                    service.tasks().insert(
                        tasklist=target_id, body=new_body
                    ).execute()

                    # Delete from source
                    service.tasks().delete(
                        tasklist=list_id, task=task['id']
                    ).execute()

                    return (
                        f"✅ Moved '{task['title']}'\n"
                        f"From: {list_display}\n"
                        f"To: {target_display}"
                    )

        return f"No pending task matching '{title_search}' found."
    except Exception as e:
        return f"Error moving task: {str(e)}"


def tasks_inbox_process():
    """
    Show all Main List tasks one by one for processing.
    Returns a formatted list with suggested destination lists
    so Mason can say 'move X to Home' etc.
    """
    try:
        print("  [TOOL] Processing inbox")
        service = get_tasks_service()

        # Find Main List (or first list)
        inbox_id, inbox_display = find_list_by_name(service, "main")
        if not inbox_id:
            all_lists = get_all_task_lists(service)
            if not all_lists:
                return "No task lists found."
            inbox_id, inbox_display = all_lists[0]

        result = service.tasks().list(
            tasklist=inbox_id, maxResults=100, showCompleted=False
        ).execute()
        items = [t for t in result.get('items', []) if t.get('status') == 'needsAction']

        if not items:
            return f"✅ Your {inbox_display} is empty — nothing to process!"

        content = f"📥 INBOX PROCESSING — {inbox_display} ({len(items)} items):\n\n"
        content += "For each item, say 'move [task] to [list name]' or 'complete [task]' or 'delete [task]'\n\n"

        for t in items:
            title   = t.get('title', '(no title)')
            due     = t.get('due', '')
            due_str = f" — due {format_due_date(due)}" if due else ""
            suggested = guess_task_list(title)
            suggestion = f"\n  💡 Suggested: {suggested}" if suggested else ""
            content += f"• {title}{due_str}{suggestion}\n"

        content += f"\n\nAvailable lists:\n"
        content += "\n".join(f"• {name}" for name in LIFE_AREA_LISTS.keys())

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error processing inbox: {str(e)}"


def tasks_list_summary():
    """
    One-shot snapshot of all task lists — pending counts, overdue count,
    and the oldest overdue item per list. Morning awareness view.
    """
    try:
        print("  [TOOL] Getting task list summary")
        service = get_tasks_service()
        all_lists = get_all_task_lists(service)
        today = datetime.date.today()

        content = f"📊 TASKS SUMMARY ({today.strftime('%A, %B %-d')}):\n"
        total_pending  = 0
        total_overdue  = 0

        for list_id, title in all_lists:
            result = service.tasks().list(
                tasklist=list_id, maxResults=100, showCompleted=False
            ).execute()
            items = [t for t in result.get('items', []) if t.get('status') == 'needsAction']

            pending  = len(items)
            overdue_items = [t for t in items if is_overdue(t.get('due', ''))]
            overdue  = len(overdue_items)
            total_pending += pending
            total_overdue += overdue

            if pending == 0:
                content += f"\n✅ {title}: empty"
                continue

            overdue_str = f" ⚠️ {overdue} overdue" if overdue else ""
            content += f"\n📋 {title}: {pending} pending{overdue_str}"

            # Show oldest overdue item if any
            if overdue_items:
                # Sort by due date ascending to find oldest
                oldest = sorted(
                    overdue_items,
                    key=lambda t: t.get('due', '9999')
                )[0]
                days = days_overdue(oldest.get('due', ''))
                content += f"\n   Most overdue: '{oldest.get('title', '')}' ({days}d)"

        content += f"\n\n📈 Total: {total_pending} pending"
        if total_overdue:
            content += f", {total_overdue} overdue ⚠️"

        return wrap_display(content.strip())
    except Exception as e:
        return f"Error getting summary: {str(e)}"


def tasks_suggest_list(title):
    """
    Suggest the best life-area list for a task based on its title.
    Used by agent when Mason adds a task without specifying a list.
    """
    suggested = guess_task_list(title)
    if suggested:
        return f"💡 Based on '{title}', I'd suggest adding this to **{suggested}**. Want me to add it there, or a different list?"
    else:
        lists = "\n".join(f"• {name}" for name in LIFE_AREA_LISTS.keys())
        return f"Which list should I add '{title}' to?\n\n{lists}\n\nOr say 'Main List' to keep it in your inbox."


if __name__ == "__main__":
    # Quick test
    print(tasks_list_all())
    print(tasks_due_today())
    print(tasks_overdue())