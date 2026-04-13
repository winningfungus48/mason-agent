import type { AllDayEvent } from '../constants/commandCenterMock'
import type { CalendarEvent } from '../constants/mockData'
import { apiJson } from './client'

export type TodayCalendarResponse = {
  dateLabel: string
  events: CalendarEvent[]
  allDayEvents: AllDayEvent[]
}

type CalendarTodayApi = {
  date: string
  all_day_events: { id?: string; title: string; calendar: string; color: string }[]
  events: {
    id?: string
    title: string
    start: string
    end: string
    calendar: string
    color_hex: string
  }[]
}

function formatHm(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false })
}

export async function fetchTodayCalendar(): Promise<TodayCalendarResponse> {
  const data = await apiJson<CalendarTodayApi>('/calendar/today')
  const dateLabel = new Date(`${data.date}T12:00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
  const events: CalendarEvent[] = data.events.map((e, i) => ({
    id: e.id || `ev-${i}`,
    title: e.title,
    startTime: formatHm(e.start),
    endTime: formatHm(e.end),
    calendarName: e.calendar,
    color: e.color_hex,
  }))
  const allDayEvents: AllDayEvent[] = data.all_day_events.map((e, i) => ({
    id: e.id || `ad-${i}`,
    title: e.title,
    color: e.color,
  }))
  return { dateLabel, events, allDayEvents }
}

type CalendarDayApi = CalendarTodayApi

function mapTimedEvents(data: CalendarDayApi): Pick<
  CalendarEvent,
  'title' | 'startTime' | 'endTime' | 'color' | 'calendarName'
>[] {
  return data.events.map((e) => ({
    title: e.title,
    startTime: formatHm(e.start),
    endTime: formatHm(e.end),
    color: e.color_hex,
    calendarName: e.calendar,
  }))
}

export async function fetchTomorrowPreviewBlock(): Promise<{
  dateLabel: string
  events: Pick<CalendarEvent, 'title' | 'startTime' | 'endTime' | 'color'>[]
}> {
  const data = await apiJson<CalendarDayApi>('/calendar/tomorrow')
  const dateLabel = new Date(`${data.date}T12:00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
  const events = mapTimedEvents(data).map(({ title, startTime, endTime, color }) => ({
    title,
    startTime,
    endTime,
    color,
  }))
  return { dateLabel, events }
}
