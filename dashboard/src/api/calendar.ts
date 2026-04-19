import type { AllDayEvent } from '../constants/commandCenterMock'
import type { CalendarEvent } from '../constants/mockData'
import { todayIsoDate } from '../utils/date'
import { ApiError, apiJson } from './client'

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

export function formatCalendarClock(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false })
}

function mapDayApi(data: CalendarTodayApi): TodayCalendarResponse {
  const dateLabel = new Date(`${data.date}T12:00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
  const events: CalendarEvent[] = data.events.map((e, i) => ({
    id: e.id || `ev-${i}`,
    title: e.title,
    startTime: formatCalendarClock(e.start),
    endTime: formatCalendarClock(e.end),
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

/**
 * Single-day calendar. Uses `/calendar/today` when the date is today so the UI works
 * even if `/calendar/day` is unavailable; other dates require GET /calendar/day on the API.
 */
export async function fetchCalendarDay(isoDate: string): Promise<TodayCalendarResponse> {
  if (isoDate === todayIsoDate()) {
    return fetchTodayCalendar()
  }
  try {
    const data = await apiJson<CalendarTodayApi>(
      `/calendar/day?date=${encodeURIComponent(isoDate)}`,
    )
    return mapDayApi(data)
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      throw new ApiError(
        404,
        'This date needs GET /calendar/day on the API. Pull latest mason-agent on the server and restart mason-api.',
      )
    }
    throw e
  }
}

export async function fetchTodayCalendar(): Promise<TodayCalendarResponse> {
  const data = await apiJson<CalendarTodayApi>('/calendar/today')
  return mapDayApi(data)
}

export type ApiMergedEvent = {
  id: string
  title: string
  start: string
  end: string
  calendar: string
  color_hex: string
  description?: string
  all_day: boolean
}

export type WeekCalendarResponse = {
  start: string
  days: Record<string, ApiMergedEvent[]>
}

export async function fetchCalendarWeek(weekStartIso: string): Promise<WeekCalendarResponse> {
  return apiJson<WeekCalendarResponse>(
    `/calendar/week?start=${encodeURIComponent(weekStartIso)}`,
  )
}

export type MonthCalendarResponse = {
  year: number
  month: number
  days: Record<string, ApiMergedEvent[]>
}

export async function fetchCalendarMonth(year: number, month: number): Promise<MonthCalendarResponse> {
  return apiJson<MonthCalendarResponse>(
    `/calendar/month?year=${year}&month=${month}`,
  )
}

type CalendarDayApi = CalendarTodayApi

function mapTimedEvents(data: CalendarDayApi): Pick<
  CalendarEvent,
  'title' | 'startTime' | 'endTime' | 'color' | 'calendarName'
>[] {
  return data.events.map((e) => ({
    title: e.title,
    startTime: formatCalendarClock(e.start),
    endTime: formatCalendarClock(e.end),
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
