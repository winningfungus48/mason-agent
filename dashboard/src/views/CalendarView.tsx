import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  type ApiMergedEvent,
  fetchCalendarDay,
  fetchCalendarMonth,
  fetchCalendarWeek,
  formatCalendarClock,
} from '../api/calendar'
import { DaySchedulePanel } from '../components/calendar/DaySchedulePanel'
import { ConnectGoogleBanner } from '../components/ConnectGoogleBanner'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { CalendarEvent } from '../constants/mockData'
import { appContent } from '../content/appContent'
import { addDays, addMonths, mondayIndex, startOfWeekMonday, toIsoDateLocal } from '../utils/date'

type ViewMode = 'day' | 'week' | 'month'

function sortEventsByTime(events: CalendarEvent[]) {
  return [...events].sort((a, b) => a.startTime.localeCompare(b.startTime))
}

function mergedToCalendarEvents(dayKey: string, items: ApiMergedEvent[]): CalendarEvent[] {
  const out: CalendarEvent[] = []
  let i = 0
  for (const e of items) {
    if (e.all_day) continue
    out.push({
      id: e.id || `${dayKey}-${i++}`,
      title: e.title,
      startTime: formatCalendarClock(e.start),
      endTime: formatCalendarClock(e.end),
      calendarName: e.calendar,
      color: e.color_hex,
    })
  }
  return sortEventsByTime(out)
}

function mergedAllDay(items: ApiMergedEvent[]) {
  return items.filter((e) => e.all_day).map((e, i) => ({
    id: e.id || `ad-${i}`,
    title: e.title,
    color: e.color_hex,
  }))
}

export function CalendarView() {
  const [mode, setMode] = useState<ViewMode>('day')
  const [cursor, setCursor] = useState(() => new Date())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [dayData, setDayData] = useState<{
    dateLabel: string
    events: CalendarEvent[]
    allDayEvents: { id: string; title: string; color: string }[]
  } | null>(null)

  const [weekData, setWeekData] = useState<{
    start: string
    days: Record<string, ApiMergedEvent[]>
  } | null>(null)

  const [monthData, setMonthData] = useState<{
    year: number
    month: number
    days: Record<string, ApiMergedEvent[]>
  } | null>(null)

  const dayIso = useMemo(() => toIsoDateLocal(cursor), [cursor])
  const weekStartIso = useMemo(() => toIsoDateLocal(startOfWeekMonday(cursor)), [cursor])
  const monthY = cursor.getFullYear()
  const monthM = cursor.getMonth() + 1

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (mode === 'day') {
        const d = await fetchCalendarDay(dayIso)
        setDayData({
          dateLabel: d.dateLabel,
          events: sortEventsByTime(d.events),
          allDayEvents: d.allDayEvents,
        })
        setWeekData(null)
        setMonthData(null)
      } else if (mode === 'week') {
        const w = await fetchCalendarWeek(weekStartIso)
        setWeekData(w)
        setDayData(null)
        setMonthData(null)
      } else {
        const m = await fetchCalendarMonth(monthY, monthM)
        setMonthData(m)
        setDayData(null)
        setWeekData(null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load calendar')
      setDayData(null)
      setWeekData(null)
      setMonthData(null)
    } finally {
      setLoading(false)
    }
  }, [mode, dayIso, weekStartIso, monthY, monthM])

  useEffect(() => {
    void load()
  }, [load])

  function goPrev() {
    setCursor((c) => {
      if (mode === 'day') return addDays(c, -1)
      if (mode === 'week') return addDays(c, -7)
      return addMonths(c, -1)
    })
  }

  function goNext() {
    setCursor((c) => {
      if (mode === 'day') return addDays(c, 1)
      if (mode === 'week') return addDays(c, 7)
      return addMonths(c, 1)
    })
  }

  function goToday() {
    setCursor(new Date())
  }

  const navLabel = useMemo(() => {
    if (mode === 'day') {
      return new Date(`${dayIso}T12:00:00`).toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    }
    if (mode === 'week') {
      const start = new Date(`${weekStartIso}T12:00:00`)
      const end = addDays(start, 6)
      return `${start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`
    }
    return new Date(monthY, monthM - 1, 1).toLocaleDateString(undefined, {
      month: 'long',
      year: 'numeric',
    })
  }, [mode, dayIso, weekStartIso, monthY, monthM])

  const monthGrid = useMemo(() => {
    if (mode !== 'month' || !monthData) return null
    const y = monthData.year
    const m = monthData.month
    const first = new Date(y, m - 1, 1)
    const lastDate = new Date(y, m, 0).getDate()
    const pad = mondayIndex(first)
    const cells: { label: number | null; iso: string | null; count: number }[] = []
    for (let i = 0; i < pad; i++) {
      cells.push({ label: null, iso: null, count: 0 })
    }
    for (let d = 1; d <= lastDate; d++) {
      const iso = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      const items = monthData.days[iso] ?? []
      cells.push({ label: d, iso, count: items.length })
    }
    const tail = (7 - ((pad + lastDate) % 7)) % 7
    for (let i = 0; i < tail; i++) {
      cells.push({ label: null, iso: null, count: 0 })
    }
    return cells
  }, [mode, monthData])

  return (
    <div className="flex min-h-0 flex-1 flex-col px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <ConnectGoogleBanner />

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">{appContent.calendar.pageTitle}</h1>
        <div className="flex rounded-lg border border-[#1f2430] bg-[#0c0e12] p-0.5">
          {(['day', 'week', 'month'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition ${
                mode === m ? 'bg-[#12151c] text-teal-300' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {appContent.calendar.modes[m]}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-b border-[#1f2430] pb-3">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={goPrev}
            className="rounded-lg px-3 py-2 text-sm text-zinc-400 hover:bg-[#12151c] hover:text-zinc-200"
            aria-label={appContent.calendar.prevAria}
          >
            ‹
          </button>
          <button
            type="button"
            onClick={goNext}
            className="rounded-lg px-3 py-2 text-sm text-zinc-400 hover:bg-[#12151c] hover:text-zinc-200"
            aria-label={appContent.calendar.nextAria}
          >
            ›
          </button>
        </div>
        <p className="min-w-0 flex-1 text-center text-sm font-medium text-zinc-300 sm:text-base">
          {navLabel}
        </p>
        <button
          type="button"
          onClick={goToday}
          className="rounded-lg border border-[#2a3142] px-3 py-1.5 text-xs font-medium text-zinc-400 hover:border-teal-500/40 hover:text-teal-300"
        >
          {appContent.calendar.today}
        </button>
      </div>

      {loading ? (
        <div className="mt-6">
          <SectionSkeleton rows={6} />
        </div>
      ) : error ? (
        <div className="mt-6 space-y-2">
          <LoadErrorCard label={error || appContent.calendar.loadError} />
        </div>
      ) : mode === 'day' && dayData ? (
        <div className="mt-6">
          <DaySchedulePanel
            dateLabel={dayData.dateLabel}
            allDayEvents={dayData.allDayEvents}
            events={dayData.events}
          />
        </div>
      ) : mode === 'week' && weekData ? (
        <div className="mt-6 space-y-4">
          {(Object.keys(weekData.days).length > 0
            ? Object.keys(weekData.days).sort()
            : Array.from({ length: 7 }, (_, i) =>
                toIsoDateLocal(addDays(new Date(`${weekStartIso}T12:00:00`), i)),
              )
          ).map((key) => {
            const items = weekData.days[key] ?? []
            const label = new Date(`${key}T12:00:00`).toLocaleDateString(undefined, {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })
            const timed = mergedToCalendarEvents(key, items)
            const allDay = mergedAllDay(items)
            return (
              <div key={key} className="rounded-2xl border border-[#1f2430] bg-[#12151c]/60 p-3">
                <p className="text-sm font-semibold text-teal-300/90">{label}</p>
                {items.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-500">{appContent.calendar.noEvents}</p>
                ) : (
                  <div className="mt-2">
                    <DaySchedulePanel
                      allDayEvents={allDay}
                      events={timed}
                      compact
                      hideHeader
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : mode === 'month' && monthData && monthGrid ? (
        <div className="mt-6 space-y-6">
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              {appContent.calendar.monthGridLabel}
            </p>
            <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-medium uppercase text-zinc-500">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
                <div key={d}>{d}</div>
              ))}
            </div>
            <div className="mt-1 grid grid-cols-7 gap-1">
              {monthGrid.map((cell, idx) => (
                <div
                  key={idx}
                  className={`flex min-h-[40px] flex-col items-center justify-start rounded-lg border border-[#1f2430]/80 py-1 text-sm ${
                    cell.label == null ? 'border-transparent bg-transparent' : 'bg-[#0c0e12]'
                  }`}
                >
                  {cell.label != null ? (
                    <>
                      <span className={cell.count > 0 ? 'font-semibold text-zinc-100' : 'text-zinc-500'}>
                        {cell.label}
                      </span>
                      {cell.count > 0 ? (
                        <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-teal-500" aria-hidden />
                      ) : null}
                    </>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              {appContent.calendar.eventsThisMonth}
            </p>
            <div className="space-y-4">
              {Object.keys(monthData.days)
                .sort()
                .filter((k) => (monthData.days[k]?.length ?? 0) > 0)
                .map((key) => {
                  const items = monthData.days[key] ?? []
                  const label = new Date(`${key}T12:00:00`).toLocaleDateString(undefined, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })
                  const timed = mergedToCalendarEvents(key, items)
                  const allDay = mergedAllDay(items)
                  return (
                    <div key={key} className="rounded-2xl border border-[#1f2430] bg-[#12151c]/60 p-3">
                      <p className="text-sm font-semibold text-teal-300/90">{label}</p>
                      <div className="mt-2">
                        <DaySchedulePanel allDayEvents={allDay} events={timed} compact hideHeader />
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-6 text-sm text-zinc-500">{appContent.calendar.noData}</div>
      )}
    </div>
  )
}
