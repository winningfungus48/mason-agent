/**
 * Command Center placeholder data. Swap `fetchCommandCenterFeed()` in HomeView for API.
 */
import type { CalendarEvent, Reminder, TaskItem } from './mockData'

export const COMMAND_CENTER_SUMMARY_PLACEHOLDER =
  '3 tasks due · 2 chores pending · workout not logged'

export type AllDayEvent = {
  id: string
  title: string
  color: string
}

export const mockAllDayEvents: AllDayEvent[] = [
  { id: 'ad1', title: 'Spring planning (all hands)', color: '#34d399' },
  { id: 'ad2', title: 'Out of office — partial', color: '#a78bfa' },
]

export type CommandBriefExpanded = {
  city: string
  tempF: number
  condition: string
  highF: number
  lowF: number
  headlines: string[]
  sports: string[]
  lastUpdatedLabel: string
}

/** Expanded morning brief (placeholder). */
export const mockBriefExpanded: CommandBriefExpanded = {
  city: 'Austin',
  tempF: 68,
  condition: 'Partly cloudy',
  highF: 72,
  lowF: 58,
  headlines: [
    'Markets steady overnight; futures slightly green.',
    'Local transit running on schedule system-wide.',
    'No severe weather alerts in your region today.',
  ],
  sports: [
    'Rangers 4, Astros 2 — final',
    'NBA: West standings tight after last night’s games',
    'F1: next race weekend preview on the wire',
  ],
  lastUpdatedLabel: '6:02 AM',
}

export const mockTomorrowDateLabel = 'Monday, April 14, 2026'

export const mockTomorrowEvents: Pick<CalendarEvent, 'title' | 'startTime' | 'endTime' | 'color' | 'calendarName'>[] = [
  {
    title: 'Sprint planning',
    startTime: '09:00',
    endTime: '10:00',
    color: '#22d3ee',
    calendarName: 'Work',
  },
  {
    title: 'Gym',
    startTime: '17:30',
    endTime: '18:30',
    color: '#f472b6',
    calendarName: 'Health',
  },
  {
    title: 'Call — dentist follow-up',
    startTime: '11:15',
    endTime: '11:45',
    color: '#34d399',
    calendarName: 'Health',
  },
]

export const mockTomorrowTasks: Pick<TaskItem, 'id' | 'title' | 'priority'>[] = [
  { id: 'tm1', title: 'Submit quarterly report', priority: 'high' },
  { id: 'tm2', title: 'Pick up dry cleaning', priority: 'medium' },
]

/** Minutes from midnight for timeline ordering. */
export function timeToMinutes(hhmm: string) {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + (m || 0)
}

/** Timeline reminders with explicit sort keys. */
export const mockTimelineReminders: (Reminder & { sortMinutes: number })[] = [
  {
    id: 'tr1',
    icon: '🔔',
    text: 'Standup in 15 minutes',
    when: 'Today · 9:45 AM',
    sortMinutes: timeToMinutes('09:45'),
  },
  {
    id: 'tr2',
    icon: '⏰',
    text: 'Take meds with food',
    when: 'Today · 12:30 PM',
    sortMinutes: timeToMinutes('12:30'),
  },
]

/** Suggested times for chore blocks (display + sort) — first two chores from `/chores/today`. */
export const CHORE_TIMELINE_SLOTS: { choreIndex: number; minutes: number }[] = [
  { choreIndex: 0, minutes: timeToMinutes('08:00') },
  { choreIndex: 1, minutes: timeToMinutes('19:00') },
]

export const HABIT_BLOCK = {
  morning: { minutes: timeToMinutes('07:00'), label: 'MORNING CHECK-IN' as const },
  evening: { minutes: timeToMinutes('20:00'), label: 'EVENING CHECK-IN' as const },
}

export const TASKS_BLOCK_MINUTES = timeToMinutes('17:00')
