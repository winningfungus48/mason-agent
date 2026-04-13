import { useState } from 'react'
import type { CalendarEvent, TaskItem } from '../../constants/mockData'

type TomorrowPreviewProps = {
  dateLabel: string
  events: Pick<CalendarEvent, 'title' | 'startTime' | 'endTime' | 'color'>[]
  tasks: Pick<TaskItem, 'id' | 'title' | 'priority'>[]
  className?: string
}

const priorityDot = {
  high: 'bg-red-500',
  medium: 'bg-amber-400',
  low: 'bg-zinc-500',
} as const

export function TomorrowPreview({
  dateLabel,
  events,
  tasks,
  className = '',
}: TomorrowPreviewProps) {
  const [open, setOpen] = useState(false)

  return (
    <section
      className={`rounded-2xl border border-[#1f2430] bg-[#12151c] ${className}`}
      aria-label="Tomorrow preview"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full min-h-[48px] items-center justify-between gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Tomorrow
          </p>
          <p className="text-sm font-medium text-zinc-200">{dateLabel}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {events.length} events · {tasks.length} tasks due
          </p>
        </div>
        <span className="text-zinc-500">{open ? '▾' : '▸'}</span>
      </button>

      {open && (
        <div className="motion-safe:animate-[cos-brief-expand_0.2s_ease-out] border-t border-[#1f2430] px-4 pb-4 pt-2">
          <h3 className="text-xs font-semibold text-zinc-500">Events</h3>
          <ul className="mt-2 space-y-2">
            {events.map((ev, i) => (
              <li key={`${ev.title}-${i}`} className="flex gap-2 text-sm text-zinc-300">
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: ev.color }}
                />
                <span>
                  <span className="font-medium">{ev.title}</span>
                  <span className="block text-xs text-zinc-500">
                    {ev.startTime}–{ev.endTime}
                  </span>
                </span>
              </li>
            ))}
          </ul>
          <h3 className="mt-4 text-xs font-semibold text-zinc-500">Tasks</h3>
          <ul className="mt-2 space-y-2">
            {tasks.map((t) => (
              <li key={t.id} className="flex items-center gap-2 text-sm text-zinc-300">
                <span className={`h-2 w-2 rounded-full ${priorityDot[t.priority]}`} />
                {t.title}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
