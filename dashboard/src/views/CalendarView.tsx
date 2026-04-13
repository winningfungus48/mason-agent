import { useEffect, useState } from 'react'
import { fetchTodayCalendar } from '../api/calendar'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { CalendarEvent } from '../constants/mockData'

function sortEventsByTime(events: CalendarEvent[]) {
  return [...events].sort((a, b) => a.startTime.localeCompare(b.startTime))
}

export function CalendarView() {
  const [dateLabel, setDateLabel] = useState('')
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchTodayCalendar()
      .then((res) => {
        if (cancelled) return
        setDateLabel(res.dateLabel)
        setEvents(sortEventsByTime(res.events))
        setError(null)
      })
      .catch((e: Error) => {
        if (cancelled) return
        setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="px-4 pb-6 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={5} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 pb-6 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load calendar" />
      </div>
    )
  }

  return (
    <div className="px-4 pb-6 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <p className="text-3xl font-semibold leading-tight tracking-tight text-teal-300/95 sm:text-4xl">
        {dateLabel}
      </p>
      <p className="mt-1 text-sm text-zinc-500">Today&apos;s schedule</p>

      {events.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-dashed border-[#2a3142] bg-[#12151c]/80 px-6 py-16 text-center">
          <p className="text-lg text-zinc-400">No events today</p>
          <p className="mt-2 text-sm text-zinc-600">Enjoy the open time — or add something in Calendar.</p>
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {events.map((ev) => (
            <li
              key={ev.id}
              className="overflow-hidden rounded-2xl border border-[#1f2430] bg-[#12151c]"
            >
              <div className="flex min-h-[56px]">
                <div
                  className="w-1.5 shrink-0"
                  style={{ backgroundColor: ev.color }}
                  aria-hidden
                />
                <div className="min-w-0 flex-1 p-4">
                  <p className="text-base font-semibold text-zinc-100">{ev.title}</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {ev.startTime}–{ev.endTime} · {ev.calendarName}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
