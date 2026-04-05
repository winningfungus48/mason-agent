"""
agents/calendar_agent.py
------------------------
Google Calendar service module for Mason's Personal Agent.
All calendar functions extracted from agent.py.
Uses core/google_auth.py for OAuth and core/config.py for constants.
"""

import os
import datetime
import zoneinfo
import re
import json
from core.google_auth import get_service
from core.config import (
    DOCUMENTS_DIR, TIMEZONE, COLOR_CATEGORY_MAP, COLOR_KEYWORDS
)
from core.display import wrap_display



def get_calendar_service():
    """Return authenticated Google Calendar service via shared auth."""
    return get_service("calendar", "v3")

def get_all_calendar_ids(service):
    """Get all calendar IDs the user has access to including shared ones."""
    try:
        calendar_list = service.calendarList().list().execute()
        return [
            (cal['id'], cal.get('summary', 'Unknown'))
            for cal in calendar_list.get('items', [])
            if cal.get('accessRole') in ['owner', 'writer', 'reader', 'freeBusyReader']
        ]
    except Exception:
        return [('primary', 'Primary')]

def format_event_time(event):
    """Safely format event start time handling both timed and all-day events."""
    start = event['start'].get('dateTime', event['start'].get('date', ''))
    if 'T' in start:
        dt_str = start[:19]
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%I:%M %p')
    else:
        return 'All day'

def get_houston_day_bounds():
    """Return start and end of today in Houston time (America/Chicago) as UTC ISO strings."""
    houston_tz = zoneinfo.ZoneInfo(TIMEZONE)
    today_houston = datetime.datetime.now(houston_tz).date()
    start_local = datetime.datetime(today_houston.year, today_houston.month, today_houston.day, 0, 0, 0, tzinfo=houston_tz)
    end_local = datetime.datetime(today_houston.year, today_houston.month, today_houston.day, 23, 59, 59, tzinfo=houston_tz)
    return start_local.isoformat(), end_local.isoformat(), today_houston

def build_rrule(recurrence_description):
    """
    Convert natural language recurrence description to an RRULE string.
    Returns (rrule_string, human_readable) or (None, error_message).
    """
    desc = recurrence_description.lower().strip()

    # Remove recurrence
    if "remove" in desc or "stop" in desc or "no repeat" in desc or "once" in desc:
        return "REMOVE", "removed recurrence (one-time event)"

    # Day mapping
    DAY_MAP = {
        "monday": "MO", "tuesday": "TU", "wednesday": "WE",
        "thursday": "TH", "friday": "FR", "saturday": "SA", "sunday": "SU",
        "mon": "MO", "tue": "TU", "wed": "WE", "thu": "TH",
        "fri": "FR", "sat": "SA", "sun": "SU"
    }

    # Parse frequency
    freq = None
    byday = []
    until = None
    count = None

    if "weekday" in desc or "every weekday" in desc:
        freq = "WEEKLY"
        byday = ["MO", "TU", "WE", "TH", "FR"]
    elif "weekend" in desc:
        freq = "WEEKLY"
        byday = ["SA", "SU"]
    elif "daily" in desc or "every day" in desc:
        freq = "DAILY"
    elif "monthly" in desc or "every month" in desc:
        freq = "MONTHLY"
    elif "annually" in desc or "every year" in desc or "yearly" in desc:
        freq = "YEARLY"
    elif "weekly" in desc or "every week" in desc:
        freq = "WEEKLY"
    elif "every" in desc:
        # Try to find a day name after "every"
        for day_name, day_code in DAY_MAP.items():
            if day_name in desc:
                freq = "WEEKLY"
                byday.append(day_code)
                break
        if not freq:
            freq = "WEEKLY"

    if not freq:
        freq = "WEEKLY"

    # Parse specific days if weekly and no byday yet
    if freq == "WEEKLY" and not byday:
        for day_name, day_code in DAY_MAP.items():
            if day_name in desc:
                if day_code not in byday:
                    byday.append(day_code)

    # Parse UNTIL date
    import re
    # Match patterns like "until May 20", "until May 20 2026", "until 2026-05-20"
    until_match = re.search(
        r'until\s+(\w+\s+\d{1,2}(?:\s+\d{4})?|\d{4}-\d{2}-\d{2})',
        desc
    )
    if until_match:
        until_str = until_match.group(1).strip()
        try:
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', until_str):
                until_dt = datetime.datetime.strptime(until_str, '%Y-%m-%d')
            elif re.match(r'\w+ \d{1,2} \d{4}', until_str):
                until_dt = datetime.datetime.strptime(until_str, '%B %d %Y')
            else:
                # Month Day without year — assume current year
                current_year = datetime.date.today().year
                until_dt = datetime.datetime.strptime(f"{until_str} {current_year}", '%B %d %Y')
            until = until_dt.strftime('%Y%m%dT235959Z')
        except Exception:
            pass

    # Parse COUNT ("for X weeks/times")
    count_match = re.search(r'for\s+(\d+)\s+(week|time|occurrence|day|month)', desc)
    if count_match:
        count = int(count_match.group(1))

    # Build RRULE string
    rrule = f"RRULE:FREQ={freq}"
    if byday:
        rrule += f";BYDAY={','.join(byday)}"
    if until:
        rrule += f";UNTIL={until}"
    elif count:
        rrule += f";COUNT={count}"

    # Build human readable
    human = f"repeats {freq.lower()}"
    if byday:
        day_names = [k for k, v in DAY_MAP.items() if v in byday and len(k) > 3]
        human += f" on {', '.join(day_names)}"
    if until:
        human += f" until {until_match.group(1) if until_match else 'end date'}"
    elif count:
        human += f" for {count} occurrences"

    return rrule, human

def calendar_set_recurrence(search_term, recurrence_description, date=None, calendar_name=None):
    """Set, change, or remove recurrence on an existing event."""
    try:
        print(f"  [TOOL] Setting recurrence on: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date, calendar_name=calendar_name)

        if not matches:
            return f"No events found matching '{search_term}'."

        # If multiple matches from same recurring series, use parent
        recurring_ids = set(e.get('recurringEventId') for e in matches if e.get('recurringEventId'))

        if len(matches) > 1 and not recurring_ids:
            names = "\n".join(f"• {e.get('summary')} on {e['start'].get('dateTime', e['start'].get('date',''))[:10]}" for e in matches[:5])
            return f"Found multiple events matching '{search_term}':\n{names}\n\nPlease add a date to be more specific."

        # Build the RRULE
        rrule, human = build_rrule(recurrence_description)

        # Get the event to modify — use parent if recurring series
        if recurring_ids:
            parent_id = list(recurring_ids)[0]
            cal_id = matches[0]['_cal_id']
            event = service.events().get(calendarId=cal_id, eventId=parent_id).execute()
            event_id = parent_id
        else:
            event = matches[0]
            cal_id = event['_cal_id']
            event_id = event['id']

        event_name = event.get('summary', search_term)

        if rrule == "REMOVE":
            # Remove recurrence — make it a one-time event
            event.pop('recurrence', None)
            service.events().update(calendarId=cal_id, eventId=event_id, body=event).execute()
            return f"✅ '{event_name}' is now a one-time event — recurrence removed."
        else:
            event['recurrence'] = [rrule]
            service.events().update(calendarId=cal_id, eventId=event_id, body=event).execute()
            return f"✅ '{event_name}' now {human}."

    except Exception as e:
        return f"Error setting recurrence: {str(e)}"

def find_events_by_search(service, search_term, date=None, calendar_name=None):
    """Search for events across calendars by title keyword and optional date."""
    if calendar_name:
        cal_id, _ = find_calendar_id_by_name(service, calendar_name)
        calendars = [(cal_id, calendar_name)] if cal_id else []
    else:
        calendars = get_all_calendar_ids(service)

    houston_tz = zoneinfo.ZoneInfo(TIMEZONE)

    if date:
        start_dt = datetime.datetime(
            *[int(x) for x in date.split('-')], tzinfo=houston_tz
        )
        end_dt = start_dt + datetime.timedelta(days=1)
    else:
        now = datetime.datetime.now(houston_tz)
        end_dt = now + datetime.timedelta(days=90)
        start_dt = now - datetime.timedelta(days=7)

    matches = []
    for cal_id, cal_name in calendars:
        if not cal_id:
            continue
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            for event in result.get('items', []):
                if search_term.lower() in event.get('summary', '').lower():
                    event['_cal_id'] = cal_id
                    event['_cal_name'] = cal_name
                    matches.append(event)
        except Exception:
            continue

    return matches

PENDING_CALENDAR_UPDATE_PATH = os.path.join(DOCUMENTS_DIR, "pending_calendar_update.json")

def save_pending_update(data):
    """Save a pending calendar update to disk while waiting for Mason's choice."""
    import json
    with open(PENDING_CALENDAR_UPDATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_pending_update():
    """Load a pending calendar update from disk."""
    import json
    if not os.path.exists(PENDING_CALENDAR_UPDATE_PATH):
        return None
    with open(PENDING_CALENDAR_UPDATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_pending_update():
    """Remove the pending calendar update file."""
    if os.path.exists(PENDING_CALENDAR_UPDATE_PATH):
        os.remove(PENDING_CALENDAR_UPDATE_PATH)

def build_updated_event(event, new_title, new_date, new_time, new_duration_minutes):
    """Apply changes to an event dict and return the updated version."""
    houston_tz = zoneinfo.ZoneInfo(TIMEZONE)

    if new_title:
        event['summary'] = new_title

    if new_date or new_time or new_duration_minutes:
        existing_start = event['start'].get('dateTime', event['start'].get('date', ''))
        existing_duration = 60
        if 'dateTime' in event['start'] and 'dateTime' in event['end']:
            s = datetime.datetime.fromisoformat(event['start']['dateTime'][:19])
            e_end = datetime.datetime.fromisoformat(event['end']['dateTime'][:19])
            existing_duration = int((e_end - s).total_seconds() / 60)

        duration = new_duration_minutes or existing_duration

        if new_date and new_time:
            start_str = f"{new_date} {new_time}"
        elif new_date:
            existing_time = existing_start[11:16] if 'T' in existing_start else "00:00"
            start_str = f"{new_date} {existing_time}"
        elif new_time:
            existing_date = existing_start[:10]
            start_str = f"{existing_date} {new_time}"
        else:
            existing_date = existing_start[:10]
            existing_time = existing_start[11:16] if 'T' in existing_start else "00:00"
            start_str = f"{existing_date} {existing_time}"

        start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        start_dt = start_dt.replace(tzinfo=houston_tz)
        end_dt = start_dt + datetime.timedelta(minutes=duration)
        event['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Chicago'}
        event['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Chicago'}

    return event

def calendar_update_event(search_term, new_title=None, new_date=None, new_time=None, new_duration_minutes=None, calendar_name=None):
    try:
        print(f"  [TOOL] Updating calendar event matching: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, calendar_name=calendar_name)

        if not matches:
            return f"No events found matching '{search_term}'."

        # Check if all matches share the same recurringEventId — i.e. it's a recurring series
        recurring_ids = set(e.get('recurringEventId') for e in matches if e.get('recurringEventId'))

        if len(matches) == 1:
            # Single event — just update it
            event = matches[0]
            updated = build_updated_event(dict(event), new_title, new_date, new_time, new_duration_minutes)
            service.events().update(calendarId=event['_cal_id'], eventId=event['id'], body=updated).execute()
            changes = []
            if new_title: changes.append(f"title → '{new_title}'")
            if new_date: changes.append(f"date → {new_date}")
            if new_time: changes.append(f"time → {new_time}")
            if new_duration_minutes: changes.append(f"duration → {new_duration_minutes} min")
            return f"✅ Updated '{updated['summary']}': {', '.join(changes)}"

        if len(recurring_ids) == 1:
            # All matches are instances of the same recurring event
            # Find the target occurrence (closest to today or specified date)
            target_date = new_date or datetime.date.today().strftime('%Y-%m-%d')
            target_event = min(matches, key=lambda e: abs(
                datetime.datetime.strptime(e['start'].get('dateTime', e['start'].get('date',''))[:10], '%Y-%m-%d').date()
                - datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
            ))

            # Save pending update for when Mason makes his choice
            save_pending_update({
                "search_term": search_term,
                "cal_id": target_event['_cal_id'],
                "event_id": target_event['id'],
                "recurring_event_id": target_event.get('recurringEventId'),
                "original_start": target_event['start'].get('dateTime', target_event['start'].get('date','')),
                "target_date": target_event['start'].get('dateTime', target_event['start'].get('date',''))[:10],
                "new_title": new_title,
                "new_date": new_date,
                "new_time": new_time,
                "new_duration_minutes": new_duration_minutes,
                "event_summary": target_event.get('summary', search_term)
            })

            target_date_fmt = datetime.datetime.strptime(
                target_event['start'].get('dateTime', target_event['start'].get('date',''))[:10],
                '%Y-%m-%d'
            ).strftime('%A, %B %d')

            return (
                f"📅 '{target_event.get('summary')}' is a recurring event. Which occurrences do you want to update?\n\n"
                f"1️⃣ Just this occurrence ({target_date_fmt})\n"
                f"2️⃣ This and all future occurrences\n"
                f"3️⃣ The entire series (all past and future)\n\n"
                f"Reply with 1, 2, or 3."
            )

        # Multiple different events with same name — ask Mason to be specific
        names = "\n".join(f"• {e.get('summary')} on {e['start'].get('dateTime', e['start'].get('date',''))[:10]}" for e in matches[:5])
        return f"Found multiple different events matching '{search_term}':\n{names}\n\nPlease include a date to be more specific."

    except Exception as e:
        return f"Error updating event: {str(e)}"

def calendar_confirm_recurring_update(choice):
    """Apply a pending recurring event update based on Mason's choice."""
    try:
        print(f"  [TOOL] Applying recurring update with choice: {choice}")
        pending = load_pending_update()
        if not pending:
            return "No pending calendar update found. Please try your update request again."

        service = get_calendar_service()
        cal_id = pending['cal_id']
        event_id = pending['event_id']
        recurring_id = pending['recurring_event_id']
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")

        choice = choice.strip()

        if choice == "1":
            # Modify just this occurrence
            event = service.events().get(calendarId=cal_id, eventId=event_id).execute()
            updated = build_updated_event(
                dict(event),
                pending['new_title'],
                pending['new_date'],
                pending['new_time'],
                pending['new_duration_minutes']
            )
            service.events().update(calendarId=cal_id, eventId=event_id, body=updated).execute()
            clear_pending_update()
            return f"✅ Updated just the {pending['target_date']} occurrence of '{pending['event_summary']}'."

        elif choice == "2":
            # Modify this and all following — get the recurring parent and split
            event = service.events().get(calendarId=cal_id, eventId=event_id).execute()
            updated = build_updated_event(
                dict(event),
                pending['new_title'],
                pending['new_date'],
                pending['new_time'],
                pending['new_duration_minutes']
            )
            # Set recurringEventId so Google knows this splits the series
            updated['recurringEventId'] = recurring_id
            service.events().update(
                calendarId=cal_id,
                eventId=event_id,
                body=updated
            ).execute()
            clear_pending_update()
            return f"✅ Updated '{pending['event_summary']}' from {pending['target_date']} onwards."

        elif choice == "3":
            # Modify the entire series via the parent recurring event
            parent = service.events().get(calendarId=cal_id, eventId=recurring_id).execute()
            updated = build_updated_event(
                dict(parent),
                pending['new_title'],
                None,  # Don't change date for entire series
                pending['new_time'],
                pending['new_duration_minutes']
            )
            service.events().update(calendarId=cal_id, eventId=recurring_id, body=updated).execute()
            clear_pending_update()
            return f"✅ Updated all occurrences of '{pending['event_summary']}'."

        else:
            return "Please reply with 1, 2, or 3."

    except Exception as e:
        return f"Error applying update: {str(e)}"

def calendar_delete_event(search_term, date=None, calendar_name=None):
    try:
        print(f"  [TOOL] Deleting calendar event matching: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date, calendar_name=calendar_name)

        if not matches:
            return f"No events found matching '{search_term}'."
        if len(matches) > 1:
            names = "\n".join(f"• {e.get('summary')} on {e['start'].get('dateTime', e['start'].get('date',''))[:10]}" for e in matches)
            return f"Found multiple events matching '{search_term}':\n{names}\n\nPlease be more specific (add a date or calendar name)."

        event = matches[0]
        cal_id = event['_cal_id']
        event_id = event['id']
        event_name = event.get('summary', 'Unknown')
        event_date = event['start'].get('dateTime', event['start'].get('date', ''))[:10]

        service.events().delete(calendarId=cal_id, eventId=event_id).execute()
        return f"✅ Deleted '{event_name}' on {event_date}."
    except Exception as e:
        return f"Error deleting event: {str(e)}"

def calendar_find_free_time(duration_minutes, date_range_start, date_range_end, hours_start="08:00", hours_end="21:00"):
    try:
        print(f"  [TOOL] Finding {duration_minutes}min free slots between {date_range_start} and {date_range_end}")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        start_date = datetime.datetime.strptime(date_range_start, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(date_range_end, '%Y-%m-%d').date()
        h_start = int(hours_start.split(':')[0])
        h_end = int(hours_end.split(':')[0])

        # Fetch all events in range
        time_min = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=houston_tz).isoformat()
        time_max = datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=houston_tz).isoformat()

        all_events = []
        for cal_id, _ in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                    maxResults=100, singleEvents=True, orderBy='startTime'
                ).execute()
                all_events.extend(result.get('items', []))
            except Exception:
                continue

        # Build busy blocks
        busy = []
        for e in all_events:
            s = e['start'].get('dateTime', e['start'].get('date', ''))
            en = e['end'].get('dateTime', e['end'].get('date', ''))
            if 'T' in s and 'T' in en:
                try:
                    s_dt = datetime.datetime.fromisoformat(s[:19]).replace(tzinfo=houston_tz)
                    e_dt = datetime.datetime.fromisoformat(en[:19]).replace(tzinfo=houston_tz)
                    busy.append((s_dt, e_dt))
                except Exception:
                    continue
        busy.sort()

        # Find free slots
        free_slots = []
        current = start_date
        while current <= end_date and len(free_slots) < 3:
            day_start = datetime.datetime.combine(current, datetime.time(h_start, 0)).replace(tzinfo=houston_tz)
            day_end = datetime.datetime.combine(current, datetime.time(h_end, 0)).replace(tzinfo=houston_tz)
            slot_start = day_start

            day_busy = [(s, e) for s, e in busy if s.date() == current or e.date() == current]

            for b_start, b_end in day_busy:
                if slot_start + datetime.timedelta(minutes=duration_minutes) <= b_start:
                    free_slots.append((slot_start, slot_start + datetime.timedelta(minutes=duration_minutes)))
                    if len(free_slots) >= 3:
                        break
                slot_start = max(slot_start, b_end)

            if len(free_slots) < 3 and slot_start + datetime.timedelta(minutes=duration_minutes) <= day_end:
                free_slots.append((slot_start, slot_start + datetime.timedelta(minutes=duration_minutes)))

            current += datetime.timedelta(days=1)

        if not free_slots:
            return f"No free {duration_minutes}-minute slots found between {date_range_start} and {date_range_end} during {hours_start}-{hours_end}."

        output = f"🕐 FREE SLOTS ({duration_minutes} minutes):\n\n"
        for i, (s, e) in enumerate(free_slots[:3], 1):
            output += f"{i}️⃣ {s.strftime('%A, %B %d')} from {s.strftime('%I:%M %p')} to {e.strftime('%I:%M %p')}\n"

        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error finding free time: {str(e)}"

def calendar_get_event_details(search_term, date=None):
    try:
        print(f"  [TOOL] Getting details for: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date)

        if not matches:
            return f"No events found matching '{search_term}'."

        event = matches[0]
        start = event['start'].get('dateTime', event['start'].get('date', ''))
        end = event['end'].get('dateTime', event['end'].get('date', ''))

        if 'T' in start:
            s_dt = datetime.datetime.fromisoformat(start[:19])
            e_dt = datetime.datetime.fromisoformat(end[:19])
            duration = int((e_dt - s_dt).total_seconds() / 60)
            time_str = s_dt.strftime('%A, %B %d at %I:%M %p')
            dur_str = f"{duration} minutes"
        else:
            time_str = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%A, %B %d (all day)')
            dur_str = "All day"

        return (
            f"📅 {event.get('summary', 'Unknown')}\n"
            f"🕐 {time_str}\n"
            f"⏱ {dur_str}\n"
            f"📆 Calendar: {event.get('_cal_name', 'Primary')}"
        )
    except Exception as e:
        return f"Error getting event details: {str(e)}"

def calendar_add_reminder(search_term, minutes_before=30, date=None):
    try:
        print(f"  [TOOL] Adding {minutes_before}min reminder to: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date)

        if not matches:
            return f"No events found matching '{search_term}'."

        event = matches[0]
        cal_id = event['_cal_id']
        event_id = event['id']

        event['reminders'] = {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': minutes_before}]
        }

        service.events().update(calendarId=cal_id, eventId=event_id, body=event).execute()
        return f"✅ Added {minutes_before}-minute reminder to '{event.get('summary')}'."
    except Exception as e:
        return f"Error adding reminder: {str(e)}"

def calendar_move_event(search_term, new_date, new_time=None, new_duration_minutes=None, date=None):
    try:
        print(f"  [TOOL] Moving event '{search_term}' to {new_date}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date)

        if not matches:
            return f"No events found matching '{search_term}'."
        if len(matches) > 1:
            recurring_ids = set(e.get('recurringEventId') for e in matches if e.get('recurringEventId'))
            if not recurring_ids:
                names = "\n".join(f"• {e.get('summary')} on {e['start'].get('dateTime', e['start'].get('date',''))[:10]}" for e in matches[:5])
                return f"Found multiple events matching '{search_term}':\n{names}\n\nPlease add a date to be more specific."

        event = matches[0]
        cal_id = event['_cal_id']
        event_id = event['id']

        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")

        existing_start = event['start'].get('dateTime', event['start'].get('date', ''))
        existing_duration = 60
        if 'dateTime' in event['start'] and 'dateTime' in event['end']:
            s = datetime.datetime.fromisoformat(event['start']['dateTime'][:19])
            e_end = datetime.datetime.fromisoformat(event['end']['dateTime'][:19])
            existing_duration = int((e_end - s).total_seconds() / 60)
            existing_time = existing_start[11:16]
        else:
            existing_time = None

        duration = new_duration_minutes or existing_duration
        time = new_time or existing_time

        if time:
            start_dt = datetime.datetime.strptime(f"{new_date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=houston_tz)
            end_dt = start_dt + datetime.timedelta(minutes=duration)
            event['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Chicago'}
            event['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Chicago'}
        else:
            end_date = (datetime.datetime.strptime(new_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            event['start'] = {'date': new_date}
            event['end'] = {'date': end_date}

        service.events().update(calendarId=cal_id, eventId=event_id, body=event).execute()
        time_label = f" at {new_time}" if new_time else ""
        return f"✅ Moved '{event.get('summary')}' to {new_date}{time_label}."
    except Exception as e:
        return f"Error moving event: {str(e)}"

def calendar_duplicate_event(search_term, new_date, target_calendar, new_time=None, date=None):
    try:
        print(f"  [TOOL] Duplicating '{search_term}' to {new_date}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date)

        if not matches:
            return f"No events found matching '{search_term}'."

        source = dict(matches[0])
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")

        # Find target calendar
        cal_id, cal_display = find_calendar_id_by_name(service, target_calendar)
        if not cal_id:
            return f"Could not find calendar '{target_calendar}'."

        # Build new event
        existing_start = source['start'].get('dateTime', source['start'].get('date', ''))
        existing_duration = 60
        if 'dateTime' in source['start'] and 'dateTime' in source['end']:
            s = datetime.datetime.fromisoformat(source['start']['dateTime'][:19])
            e_end = datetime.datetime.fromisoformat(source['end']['dateTime'][:19])
            existing_duration = int((e_end - s).total_seconds() / 60)
            existing_time = new_time or existing_start[11:16]
            start_dt = datetime.datetime.strptime(f"{new_date} {existing_time}", "%Y-%m-%d %H:%M").replace(tzinfo=houston_tz)
            end_dt = start_dt + datetime.timedelta(minutes=existing_duration)
            source['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Chicago'}
            source['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Chicago'}
        else:
            end_date = (datetime.datetime.strptime(new_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            source['start'] = {'date': new_date}
            source['end'] = {'date': end_date}

        # Remove fields that shouldn't be copied
        for field in ['id', 'etag', 'iCalUID', 'recurringEventId', 'originalStartTime', 'sequence', '_cal_id', '_cal_name']:
            source.pop(field, None)

        service.events().insert(calendarId=cal_id, body=source).execute()
        return f"✅ Copied '{matches[0].get('summary')}' to {new_date} on '{cal_display}'."
    except Exception as e:
        return f"Error duplicating event: {str(e)}"

def calendar_bulk_view(start_date, end_date):
    try:
        print(f"  [TOOL] Bulk view from {start_date} to {end_date}")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        time_min = start_dt.replace(tzinfo=houston_tz).isoformat()
        time_max = (end_dt + datetime.timedelta(days=1)).replace(tzinfo=houston_tz).isoformat()

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                    maxResults=100, singleEvents=True, orderBy='startTime'
                ).execute()
                for e in result.get('items', []):
                    e['_cal_name'] = cal_name
                    all_events.append(e)
            except Exception:
                continue

        if not all_events:
            return f"No events found between {start_date} and {end_date}."

        # Group by day
        from collections import defaultdict
        days = defaultdict(list)
        for e in all_events:
            s = e['start'].get('dateTime', e['start'].get('date', ''))
            day_key = s[:10]
            days[day_key].append(e)

        output = f"📅 CALENDAR: {start_date} to {end_date}\n"
        for day in sorted(days.keys()):
            day_dt = datetime.datetime.strptime(day, '%Y-%m-%d')
            output += f"\n━━ {day_dt.strftime('%A, %B %d')} ━━\n"
            for e in sorted(days[day], key=lambda x: x['start'].get('dateTime', x['start'].get('date', ''))):
                s = e['start'].get('dateTime', e['start'].get('date', ''))
                time_str = datetime.datetime.fromisoformat(s[:19]).strftime('%I:%M %p') if 'T' in s else 'All day'
                cal_label = f" [{e.get('_cal_name','')}]" if e.get('_cal_name') and e['_cal_name'] not in ['primary', 'wrightmasonnn@gmail.com'] else ""
                output += f"  • {time_str} — {e.get('summary', 'Untitled')}{cal_label}\n"

        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error getting bulk calendar view: {str(e)}"


def guess_event_color(title):
    """Guess color category from event title keywords."""
    title_lower = title.lower()
    for category, keywords in COLOR_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return category, COLOR_CATEGORY_MAP[category]
    return None, None

def calendar_set_event_color(search_term, color_name, date=None):
    try:
        print(f"  [TOOL] Setting color on: {search_term}")
        service = get_calendar_service()
        matches = find_events_by_search(service, search_term, date=date)

        if not matches:
            return f"No events found matching '{search_term}'."

        color_key = color_name.lower().strip()
        color_info = COLOR_CATEGORY_MAP.get(color_key)
        if not color_info:
            available = ", ".join(COLOR_CATEGORY_MAP.keys())
            return f"Unknown color category '{color_name}'. Available: {available}"

        event = matches[0]
        cal_id = event['_cal_id']
        event_id = event['id']
        event['colorId'] = color_info['id']
        service.events().update(calendarId=cal_id, eventId=event_id, body=event).execute()

        return f"✅ {color_info['emoji']} Set '{event.get('summary')}' to {color_info['name']} ({color_key})."
    except Exception as e:
        return f"Error setting color: {str(e)}"

def calendar_audit_uncategorized():
    try:
        print(f"  [TOOL] Auditing uncategorized events")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        now = datetime.datetime.now(houston_tz)
        end = now + datetime.timedelta(days=14)

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id,
                    timeMin=now.isoformat(),
                    timeMax=end.isoformat(),
                    maxResults=50, singleEvents=True, orderBy='startTime'
                ).execute()
                for e in result.get('items', []):
                    e['_cal_id'] = cal_id
                    e['_cal_name'] = cal_name
                    all_events.append(e)
            except Exception:
                continue

        # Find events with no colorId
        uncolored = [e for e in all_events if not e.get('colorId')]

        if not uncolored:
            return "✅ All events in the next 14 days are categorized!"

        output = "🎨 UNCATEGORIZED EVENTS (next 14 days):\n\n"
        for e in uncolored:
            title = e.get('summary', 'Untitled')
            start = e['start'].get('dateTime', e['start'].get('date', ''))
            date_str = datetime.datetime.fromisoformat(start[:10]).strftime('%b %d') if start else '?'
            category, color_info = guess_event_color(title)
            suggestion = f"{color_info['emoji']} {category}" if color_info else "❓ unsure"
            output += f"• {date_str} — {title} → suggested: {suggestion}\n"

        output += "\nSay 'apply suggested colors' to auto-apply all, or tell me which ones to change."
        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error auditing calendar: {str(e)}"

PENDING_SMART_SCHEDULE_PATH = os.path.join(DOCUMENTS_DIR, "pending_smart_schedule.json")

def calendar_smart_schedule(task_title, duration_minutes, deadline_date, hours_start, hours_end, calendar_name=None):
    try:
        print(f"  [TOOL] Smart scheduling: {task_title}")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        today = datetime.date.today()
        deadline = datetime.datetime.strptime(deadline_date, '%Y-%m-%d').date()
        h_start = int(hours_start.split(':')[0])
        h_end = int(hours_end.split(':')[0])

        time_min = datetime.datetime.combine(today, datetime.time.min).replace(tzinfo=houston_tz).isoformat()
        time_max = datetime.datetime.combine(deadline, datetime.time.max).replace(tzinfo=houston_tz).isoformat()

        all_events = []
        for cal_id, _ in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                    maxResults=100, singleEvents=True, orderBy='startTime'
                ).execute()
                all_events.extend(result.get('items', []))
            except Exception:
                continue

        busy = []
        for e in all_events:
            s = e['start'].get('dateTime', '')
            en = e['end'].get('dateTime', '')
            if s and en:
                try:
                    busy.append((
                        datetime.datetime.fromisoformat(s[:19]).replace(tzinfo=houston_tz),
                        datetime.datetime.fromisoformat(en[:19]).replace(tzinfo=houston_tz)
                    ))
                except Exception:
                    continue
        busy.sort()

        # Find first available slot
        current = today
        slot_found = None
        while current <= deadline:
            day_start = datetime.datetime.combine(current, datetime.time(h_start, 0)).replace(tzinfo=houston_tz)
            day_end = datetime.datetime.combine(current, datetime.time(h_end, 0)).replace(tzinfo=houston_tz)
            candidate = day_start

            day_busy = [(s, e) for s, e in busy if s.date() == current]
            for b_start, b_end in day_busy:
                if candidate + datetime.timedelta(minutes=duration_minutes) <= b_start:
                    slot_found = candidate
                    break
                candidate = max(candidate, b_end)

            if not slot_found and candidate + datetime.timedelta(minutes=duration_minutes) <= day_end:
                slot_found = candidate

            if slot_found:
                break
            current += datetime.timedelta(days=1)

        if not slot_found:
            return f"No available {duration_minutes}-minute slot found before {deadline_date} during {hours_start}-{hours_end}."

        slot_end = slot_found + datetime.timedelta(minutes=duration_minutes)

        # Save pending for confirmation
        import json
        with open(PENDING_SMART_SCHEDULE_PATH, 'w') as f:
            json.dump({
                "task_title": task_title,
                "date": slot_found.strftime('%Y-%m-%d'),
                "time": slot_found.strftime('%H:%M'),
                "duration_minutes": duration_minutes,
                "calendar_name": calendar_name
            }, f)

        return (
            f"📅 Best available slot for '{task_title}':\n\n"
            f"🕐 {slot_found.strftime('%A, %B %d')} from {slot_found.strftime('%I:%M %p')} to {slot_end.strftime('%I:%M %p')}\n\n"
            f"Should I book it? Say 'yes book it' to confirm."
        )
    except Exception as e:
        return f"Error smart scheduling: {str(e)}"

def calendar_confirm_smart_schedule():
    try:
        import json
        if not os.path.exists(PENDING_SMART_SCHEDULE_PATH):
            return "No pending schedule found. Please make a new scheduling request."

        with open(PENDING_SMART_SCHEDULE_PATH, 'r') as f:
            pending = json.load(f)

        result = calendar_add_event(
            pending['task_title'],
            pending['date'],
            pending['time'],
            pending['duration_minutes'],
            calendar_name=pending.get('calendar_name')
        )
        os.remove(PENDING_SMART_SCHEDULE_PATH)
        return result
    except Exception as e:
        return f"Error confirming schedule: {str(e)}"

def calendar_conflict_report():
    try:
        print(f"  [TOOL] Running conflict report")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        now = datetime.datetime.now(houston_tz)
        end = now + datetime.timedelta(days=30)

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id, timeMin=now.isoformat(), timeMax=end.isoformat(),
                    maxResults=100, singleEvents=True, orderBy='startTime'
                ).execute()
                for e in result.get('items', []):
                    e['_cal_name'] = cal_name
                    all_events.append(e)
            except Exception:
                continue

        # Only timed events
        timed = []
        for e in all_events:
            s = e['start'].get('dateTime', '')
            en = e['end'].get('dateTime', '')
            if s and en:
                try:
                    timed.append({
                        'title': e.get('summary', 'Untitled'),
                        'start': datetime.datetime.fromisoformat(s[:19]).replace(tzinfo=houston_tz),
                        'end': datetime.datetime.fromisoformat(en[:19]).replace(tzinfo=houston_tz),
                        'cal': e.get('_cal_name', '')
                    })
                except Exception:
                    continue

        timed.sort(key=lambda x: x['start'])

        conflicts = []
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i+1]
            if a['end'] > b['start']:
                conflicts.append(f"⚠️ OVERLAP: '{a['title']}' and '{b['title']}' on {a['start'].strftime('%b %d')}")
            elif (b['start'] - a['end']).total_seconds() < 900 and a['start'].date() == b['start'].date():
                conflicts.append(f"⏱ TIGHT: '{a['title']}' ends at {a['end'].strftime('%I:%M %p')}, '{b['title']}' starts at {b['start'].strftime('%I:%M %p')} on {a['start'].strftime('%b %d')} (less than 15 min gap)")

        if not conflicts:
            return "✅ No conflicts found in the next 30 days!"

        content = "🚨 CONFLICT REPORT (next 30 days):\n\n" + "\n".join(conflicts)
        return f"[DISPLAY_RAW]\n{content}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error running conflict report: {str(e)}"

def calendar_weekly_prep():
    try:
        print(f"  [TOOL] Generating weekly prep report")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        now = datetime.datetime.now(houston_tz)
        # Next Monday
        days_to_monday = (7 - now.weekday()) % 7 or 7
        next_monday = now + datetime.timedelta(days=days_to_monday)
        next_sunday = next_monday + datetime.timedelta(days=6)

        time_min = next_monday.replace(hour=0, minute=0, second=0).isoformat()
        time_max = next_sunday.replace(hour=23, minute=59, second=59).isoformat()

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                    maxResults=50, singleEvents=True, orderBy='startTime'
                ).execute()
                for e in result.get('items', []):
                    e['_cal_name'] = cal_name
                    all_events.append(e)
            except Exception:
                continue

        no_location = [e for e in all_events if not e.get('location') and 'T' in e['start'].get('dateTime', '')]
        uncolored = [e for e in all_events if not e.get('colorId')]

        output = f"📋 WEEKLY PREP — Week of {next_monday.strftime('%B %d')}\n\n"
        output += f"📅 {len(all_events)} events next week\n\n"

        if no_location:
            output += "📍 EVENTS WITHOUT LOCATION:\n"
            for e in no_location[:5]:
                s = e['start'].get('dateTime', '')
                time_str = datetime.datetime.fromisoformat(s[:19]).strftime('%a %b %d at %I:%M %p') if s else '?'
                output += f"  • {time_str} — {e.get('summary', 'Untitled')}\n"
            output += "\n"

        if uncolored:
            output += "🎨 UNCATEGORIZED EVENTS:\n"
            for e in uncolored[:5]:
                s = e['start'].get('dateTime', e['start'].get('date', ''))
                date_str = s[:10]
                output += f"  • {date_str} — {e.get('summary', 'Untitled')}\n"
            output += "\n"

        # Conflict check for next week
        timed = []
        for e in all_events:
            s = e['start'].get('dateTime', '')
            en = e['end'].get('dateTime', '')
            if s and en:
                try:
                    timed.append({
                        'title': e.get('summary', 'Untitled'),
                        'start': datetime.datetime.fromisoformat(s[:19]).replace(tzinfo=houston_tz),
                        'end': datetime.datetime.fromisoformat(en[:19]).replace(tzinfo=houston_tz)
                    })
                except Exception:
                    continue
        timed.sort(key=lambda x: x['start'])

        week_conflicts = []
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i+1]
            if a['end'] > b['start']:
                week_conflicts.append(f"  ⚠️ '{a['title']}' overlaps '{b['title']}' on {a['start'].strftime('%b %d')}")

        if week_conflicts:
            output += "🚨 CONFLICTS:\n" + "\n".join(week_conflicts) + "\n\n"
        else:
            output += "✅ No conflicts next week\n\n"

        output += "💡 Tip: Say 'apply suggested colors' to auto-categorize uncategorized events."
        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error generating weekly prep: {str(e)}"

def get_day_of_week_date(day_reference):
    """Compute exact date for relative day references using Python datetime."""
    try:
        print(f"  [TOOL] Computing date for: {day_reference}")
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        today = datetime.datetime.now(houston_tz).date()
        ref = day_reference.lower().strip()

        DAY_NAMES = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        # Handle tomorrow / today
        if "tomorrow" in ref:
            target = today + datetime.timedelta(days=1)
            return f"Tomorrow is {target.strftime('%A, %B %d, %Y')} — use date {target.strftime('%Y-%m-%d')}"
        if ref == "today":
            return f"Today is {today.strftime('%A, %B %d, %Y')} — use date {today.strftime('%Y-%m-%d')}"

        # Find which day name is mentioned
        target_weekday = None
        for day_name, weekday_num in DAY_NAMES.items():
            if day_name in ref:
                target_weekday = weekday_num
                break

        if target_weekday is None:
            return f"Could not parse day from '{day_reference}'. Please provide an exact date like 2026-04-08."

        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday

        if "next" in ref:
            # "next Wednesday" = the Wednesday of next week
            if days_ahead <= 0:
                days_ahead += 7
            days_ahead += 7 if days_ahead < 7 else 0
        else:
            # "this Wednesday" = the coming Wednesday this week or next
            if days_ahead <= 0:
                days_ahead += 7

        target = today + datetime.timedelta(days=days_ahead)
        return f"'{day_reference}' is {target.strftime('%A, %B %d, %Y')} — use date {target.strftime('%Y-%m-%d')}"
    except Exception as e:
        return f"Error computing date: {str(e)}"

def find_calendar_id_by_name(service, calendar_name):
    """Find a calendar ID by matching name. Returns (cal_id, cal_display_name)."""
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        name_lower = calendar_name.lower().strip()
        # Try exact match first
        for cal in calendars:
            if cal.get('summary', '').lower() == name_lower:
                return cal['id'], cal['summary']
        # Try partial match
        for cal in calendars:
            if name_lower in cal.get('summary', '').lower():
                return cal['id'], cal['summary']
        return None, None
    except Exception:
        return None, None

def check_calendar_conflicts(service, cal_id, date, time, duration_minutes):
    """Check if there are existing events in the given time window."""
    try:
        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        start_dt = start_dt.replace(tzinfo=houston_tz)
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        result = service.events().list(
            calendarId=cal_id,
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        conflicts = result.get('items', [])
        return conflicts
    except Exception:
        return []

def calendar_add_event(title, date, time=None, duration_minutes=60, description=None, calendar_name=None, recurrence=None):
    try:
        print(f"  [TOOL] Adding calendar event: {title} on {date}")
        service = get_calendar_service()

        # Resolve calendar ID
        if calendar_name:
            cal_id, cal_display = find_calendar_id_by_name(service, calendar_name)
            if not cal_id:
                return f"Could not find a calendar named '{calendar_name}'."
        else:
            cal_id = 'primary'
            cal_display = 'primary'

        # Check for conflicts if timed event
        if time:
            conflicts = check_calendar_conflicts(service, cal_id, date, time, duration_minutes)
            if conflicts:
                conflict_names = ", ".join(e.get('summary', 'Unknown event') for e in conflicts)
                return f"⚠️ CONFLICT DETECTED: '{conflict_names}' already exists at that time on {cal_display}. Do you still want to add '{title}', or would you like a different time?"

        # Build event
        if time:
            start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
            event = {
                'summary': title,
                'description': description or '',
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Chicago'},
                'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Chicago'},
            }
        else:
            end_date = (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            event = {
                'summary': title,
                'description': description or '',
                'start': {'date': date},
                'end': {'date': end_date},
            }

        # Add recurrence if specified
        recurrence_label = ""
        if recurrence:
            rrule, human = build_rrule(recurrence)
            if rrule and rrule != "REMOVE":
                event['recurrence'] = [rrule]
                recurrence_label = f", {human}"

        service.events().insert(calendarId=cal_id, body=event).execute()

        # Auto-apply color based on event title
        try:
            category, color_info = guess_event_color(title)
            if color_info:
                # Re-fetch to get the event ID, then color it
                import zoneinfo as zi
                houston_tz2 = zi.ZoneInfo("America/Chicago")
                t_min = datetime.datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=houston_tz2).isoformat() if not time else None
                new_matches = find_events_by_search(service, title, date=date, calendar_name=calendar_name)
                if new_matches:
                    ev = new_matches[-1]
                    ev['colorId'] = color_info['id']
                    service.events().update(calendarId=cal_id, eventId=ev['id'], body=ev).execute()
        except Exception:
            pass  # Color failure shouldn't block event creation

        cal_label = f" on '{cal_display}' calendar" if calendar_name else ""
        recurrence_label_final = recurrence_label if recurrence else ""
        return f"✅ Added '{title}' on {date}" + (f" at {time}" if time else " (all day)") + cal_label + recurrence_label_final
    except Exception as e:
        return f"Error adding calendar event: {str(e)}"

def calendar_get_events(days_ahead=7):
    try:
        print(f"  [TOOL] Getting calendar events for next {days_ahead} days")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        import zoneinfo
        houston_tz = zoneinfo.ZoneInfo("America/Chicago")
        now_houston = datetime.datetime.now(houston_tz)
        end_houston = now_houston + datetime.timedelta(days=days_ahead)
        time_min = now_houston.isoformat()
        time_max = end_houston.isoformat()

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=20,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                for event in result.get('items', []):
                    event['_calendar_name'] = cal_name
                    all_events.append(event)
            except Exception:
                continue

        if not all_events:
            return f"No events in the next {days_ahead} days."

        all_events.sort(key=lambda e: e['start'].get('dateTime', e['start'].get('date', '')))

        output = f"📅 UPCOMING EVENTS (next {days_ahead} days):\n"
        for event in all_events:
            start = event['start'].get('dateTime', event['start'].get('date', ''))
            if 'T' in start:
                dt_str = start[:19]
                dt = datetime.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
                formatted = dt.strftime('%a %b %d at %I:%M %p')
            else:
                dt = datetime.datetime.strptime(start, '%Y-%m-%d')
                formatted = dt.strftime('%a %b %d (all day)')
            cal_label = f" [{event['_calendar_name']}]" if event['_calendar_name'] != 'primary' else ""
            output += f"• {formatted} — {event['summary']}{cal_label}\n"

        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error getting calendar events: {str(e)}"

def calendar_get_today():
    try:
        print(f"  [TOOL] Getting today's calendar events")
        service = get_calendar_service()
        calendar_ids = get_all_calendar_ids(service)

        time_min, time_max, today_houston = get_houston_day_bounds()

        all_events = []
        for cal_id, cal_name in calendar_ids:
            try:
                result = service.events().list(
                    calendarId=cal_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=10,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                for event in result.get('items', []):
                    event['_calendar_name'] = cal_name
                    all_events.append(event)
            except Exception:
                continue

        if not all_events:
            return "No events on your calendar today."

        all_events.sort(key=lambda e: e['start'].get('dateTime', e['start'].get('date', '')))

        output = f"📅 TODAY'S CALENDAR ({today_houston.strftime('%A, %B %d')}):\n"
        for event in all_events:
            formatted = format_event_time(event)
            cal_label = f" [{event['_calendar_name']}]" if event['_calendar_name'] != 'primary' else ""
            output += f"• {formatted} — {event['summary']}{cal_label}\n"

        return f"[DISPLAY_RAW]\n{output.strip()}\n[/DISPLAY_RAW]"
    except Exception as e:
        return f"Error getting today's events: {str(e)}"
