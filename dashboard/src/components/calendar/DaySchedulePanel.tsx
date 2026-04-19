import { AllDayBanner } from '../command-center/AllDayBanner'
import type { AllDayEvent } from '../../constants/commandCenterMock'
import type { CalendarEvent } from '../../constants/mockData'

type DaySchedulePanelProps = {
  dateLabel?: string
  allDayEvents: AllDayEvent[]
  events: CalendarEvent[]
  /** Smaller type/spacing (Home command center). */
  compact?: boolean
  /** Omit title + subtitle (nested day rows under week/month). */
  hideHeader?: boolean
}

export function DaySchedulePanel({
  dateLabel = '',
  allDayEvents,
  events,
  compact,
  hideHeader,
}: DaySchedulePanelProps) {
  const titleClass = compact ? 'text-sm font-medium text-zinc-300' : 'text-2xl font-semibold text-teal-300/95 sm:text-3xl'
  const emptyClass = compact
    ? 'mt-3 rounded-2xl border border-dashed border-[#2a3142] px-4 py-8 text-center text-sm text-zinc-500'
    : 'mt-8 rounded-2xl border border-dashed border-[#2a3142] bg-[#12151c]/80 px-6 py-16 text-center'

  return (
    <section aria-label="Day schedule">
      {!hideHeader && dateLabel ? (
        <>
          <p className={titleClass}>{dateLabel}</p>
          {!compact ? (
            <p className="mt-1 text-sm text-zinc-500">Google Calendar</p>
          ) : null}
        </>
      ) : null}
      <div className={hideHeader ? '' : compact ? 'mt-2' : 'mt-4'}>
        <AllDayBanner events={allDayEvents} />
      </div>
      {events.length === 0 ? (
        allDayEvents.length === 0 ? (
        <div className={emptyClass}>
          <p className={compact ? '' : 'text-lg text-zinc-400'}>No timed events</p>
          {!compact ? (
            <p className="mt-2 text-sm text-zinc-600">Enjoy the open time — or add something in Calendar.</p>
          ) : null}
        </div>
        ) : null
      ) : (
        <ul className={compact ? 'mt-3 space-y-2' : 'mt-6 space-y-3'}>
          {events.map((ev) => (
            <li
              key={ev.id}
              className="overflow-hidden rounded-2xl border border-[#1f2430] bg-[#12151c]"
            >
              <div className={`flex ${compact ? 'min-h-[48px]' : 'min-h-[56px]'}`}>
                <div
                  className="w-1.5 shrink-0"
                  style={{ backgroundColor: ev.color }}
                  aria-hidden
                />
                <div className={`min-w-0 flex-1 ${compact ? 'p-3' : 'p-4'}`}>
                  <p className={`font-semibold text-zinc-100 ${compact ? 'text-sm' : 'text-base'}`}>
                    {ev.title}
                  </p>
                  <p className={`mt-0.5 text-zinc-500 ${compact ? 'text-xs' : 'text-sm'}`}>
                    {ev.startTime}–{ev.endTime} · {ev.calendarName}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
