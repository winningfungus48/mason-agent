import type { CalendarEvent, Chore, Habit, TaskItem } from '../constants/mockData'
import type { Reminder } from '../constants/mockData'
import {
  CHORE_TIMELINE_SLOTS,
  HABIT_BLOCK,
  TASKS_BLOCK_MINUTES,
  timeToMinutes,
} from '../constants/commandCenterMock'

export type TimelineReminder = Reminder & { sortMinutes: number }

export type TimelineEntry =
  | {
      id: string
      kind: 'calendar'
      minutes: number
      endMinutes: number
      event: CalendarEvent
    }
  | { id: string; kind: 'chore'; minutes: number; chore: Chore }
  | {
      id: string
      kind: 'habit-block'
      minutes: number
      period: 'morning' | 'evening'
      label: string
      habits: Habit[]
    }
  | {
      id: string
      kind: 'tasks-block'
      minutes: number
      overdue: TaskItem[]
      dueToday: TaskItem[]
    }
  | { id: string; kind: 'reminder'; minutes: number; reminder: TimelineReminder }

export function calendarEventWindow(ev: CalendarEvent) {
  return {
    start: timeToMinutes(ev.startTime),
    end: timeToMinutes(ev.endTime),
  }
}

export function buildTimelineEntries(
  events: CalendarEvent[],
  chores: Chore[],
  habits: Habit[],
  allTasks: TaskItem[],
  timelineReminders: TimelineReminder[],
  todayIso: string,
): TimelineEntry[] {
  const entries: TimelineEntry[] = []

  for (const ev of events) {
    const { start, end } = calendarEventWindow(ev)
    entries.push({
      id: `cal-${ev.id}`,
      kind: 'calendar',
      minutes: start,
      endMinutes: end,
      event: ev,
    })
  }

  const choreById = new Map(chores.map((c) => [c.id, c]))
  for (const slot of CHORE_TIMELINE_SLOTS) {
    const c = choreById.get(slot.choreId)
    if (c) {
      entries.push({
        id: `chore-${c.id}-${slot.minutes}`,
        kind: 'chore',
        minutes: slot.minutes,
        chore: c,
      })
    }
  }

  entries.push({
    id: 'habit-morning',
    kind: 'habit-block',
    minutes: HABIT_BLOCK.morning.minutes,
    period: 'morning',
    label: HABIT_BLOCK.morning.label,
    habits,
  })

  entries.push({
    id: 'habit-evening',
    kind: 'habit-block',
    minutes: HABIT_BLOCK.evening.minutes,
    period: 'evening',
    label: HABIT_BLOCK.evening.label,
    habits,
  })

  const overdue = allTasks.filter((t) => t.dueDate < todayIso)
  const dueToday = allTasks.filter((t) => t.dueDate === todayIso)
  entries.push({
    id: 'tasks-due',
    kind: 'tasks-block',
    minutes: TASKS_BLOCK_MINUTES,
    overdue,
    dueToday,
  })

  for (const r of timelineReminders) {
    entries.push({
      id: `rem-${r.id}`,
      kind: 'reminder',
      minutes: r.sortMinutes,
      reminder: r,
    })
  }

  return entries.sort((a, b) => a.minutes - b.minutes)
}

export function formatHourLabel(totalMinutes: number) {
  const h24 = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  const d = new Date()
  d.setHours(h24, m, 0, 0)
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}

export function isCalendarCurrent(ev: CalendarEvent, nowMinutes: number) {
  const { start, end } = calendarEventWindow(ev)
  return nowMinutes >= start && nowMinutes < end
}
