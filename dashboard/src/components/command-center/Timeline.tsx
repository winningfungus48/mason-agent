import { useLayoutEffect, useMemo, useRef } from 'react'
import {
  formatHourLabel,
  isCalendarCurrent,
  type TimelineEntry,
} from '../../lib/commandCenterTimeline'

type TimelineProps = {
  entries: TimelineEntry[]
  nowMinutes: number
  todayIso: string
  morningLogged: Set<string>
  eveningLogged: Set<string>
  onToggleHabit: (period: 'morning' | 'evening', habitId: string) => void
  choreDoneOverride: Record<string, boolean>
  onChoreDone: (choreId: string) => void
  taskDoneIds: Set<string>
  onToggleTask: (taskId: string) => void
  eveningHighlight: boolean
}

function isPast(minutes: number, nowMinutes: number) {
  return minutes < nowMinutes
}

export function Timeline({
  entries,
  nowMinutes,
  todayIso,
  morningLogged,
  eveningLogged,
  onToggleHabit,
  choreDoneOverride,
  onChoreDone,
  taskDoneIds,
  onToggleTask,
  eveningHighlight,
}: TimelineProps) {
  const nowLineRef = useRef<HTMLLIElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const rows = useMemo(() => buildRenderPlan(entries, nowMinutes), [entries, nowMinutes])

  useLayoutEffect(() => {
    const sc = scrollRef.current
    const nowEl = nowLineRef.current
    if (!sc || !nowEl) return
    const target = Math.max(0, nowEl.offsetTop - sc.clientHeight * 0.2)
    sc.scrollTo({ top: target, behavior: 'smooth' })
  }, [rows.length, nowMinutes])

  return (
    <div
      ref={scrollRef}
      className="relative max-h-[min(70vh,900px)] overflow-y-auto overflow-x-hidden lg:max-h-none"
    >
      <div className="relative pl-14 pr-2 sm:pl-16">
        <div
          className="absolute bottom-0 left-[2.125rem] top-0 w-px bg-zinc-700/80 sm:left-[2.375rem]"
          aria-hidden
        />

        <ul className="space-y-0">
          {rows.map((row) => {
            if (row.type === 'hour') {
              return (
                <li key={`hour-${row.hour}`} className="relative flex min-h-[28px] items-center">
                  <span className="absolute left-0 w-12 shrink-0 text-right text-[11px] font-medium text-zinc-500 sm:w-14">
                    {row.label}
                  </span>
                </li>
              )
            }
            if (row.type === 'now') {
              return (
                <li
                  key="timeline-now"
                  ref={nowLineRef}
                  data-timeline-now
                  className="relative flex min-h-[36px] items-center py-1"
                >
                  <span className="absolute left-[1.875rem] z-10 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-teal-400 bg-[#0c0e12] shadow-[0_0_12px_rgba(45,212,191,0.6)] sm:left-[2.125rem]" />
                  <div className="absolute left-8 right-0 top-1/2 z-0 h-px bg-teal-500/60 sm:left-9" />
                  <span className="ml-auto rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-teal-300">
                    Now
                  </span>
                </li>
              )
            }

            const e = row.entry
            const past = isPast(e.minutes, nowMinutes)
            const opacity = past ? 'opacity-40' : 'opacity-100'

            return (
              <li key={e.id} className={`relative pb-6 pt-1 motion-safe:transition-opacity ${opacity}`}>
                <TimelineItemBody
                  entry={e}
                  nowMinutes={nowMinutes}
                  todayIso={todayIso}
                  morningLogged={morningLogged}
                  eveningLogged={eveningLogged}
                  onToggleHabit={onToggleHabit}
                  choreDoneOverride={choreDoneOverride}
                  onChoreDone={onChoreDone}
                  taskDoneIds={taskDoneIds}
                  onToggleTask={onToggleTask}
                  eveningHighlight={eveningHighlight}
                />
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

type Row =
  | { type: 'hour'; hour: number; label: string }
  | { type: 'now' }
  | { type: 'entry'; entry: TimelineEntry }

function buildRenderPlan(entries: TimelineEntry[], nowMinutes: number): Row[] {
  const sorted = [...entries].sort((a, b) => a.minutes - b.minutes)
  const rows: Row[] = []
  let lastHour = -1
  let nowInserted = false

  for (const entry of sorted) {
    if (!nowInserted && nowMinutes < entry.minutes) {
      rows.push({ type: 'now' })
      nowInserted = true
    }
    const h = Math.floor(entry.minutes / 60)
    if (h !== lastHour) {
      rows.push({
        type: 'hour',
        hour: h,
        label: formatHourLabel(h * 60),
      })
      lastHour = h
    }
    rows.push({ type: 'entry', entry })
  }
  if (!nowInserted) {
    rows.push({ type: 'now' })
  }
  return rows
}

const priorityDot = {
  high: 'bg-red-500',
  medium: 'bg-amber-400',
  low: 'bg-zinc-500',
} as const

function TimelineItemBody({
  entry,
  nowMinutes,
  todayIso,
  morningLogged,
  eveningLogged,
  onToggleHabit,
  choreDoneOverride,
  onChoreDone,
  taskDoneIds,
  onToggleTask,
  eveningHighlight,
}: {
  entry: TimelineEntry
  nowMinutes: number
  todayIso: string
  morningLogged: Set<string>
  eveningLogged: Set<string>
  onToggleHabit: (period: 'morning' | 'evening', habitId: string) => void
  choreDoneOverride: Record<string, boolean>
  onChoreDone: (choreId: string) => void
  taskDoneIds: Set<string>
  onToggleTask: (taskId: string) => void
  eveningHighlight: boolean
}) {
  if (entry.kind === 'calendar') {
    const ev = entry.event
    const current = isCalendarCurrent(ev, nowMinutes)
    return (
      <article
        className={`rounded-xl border border-[#1f2430] border-l-4 bg-[#0c0e12]/90 py-3 pl-3 pr-3 sm:pl-4 ${
          current ? 'shadow-[0_0_20px_rgba(45,212,191,0.12)] ring-1 ring-teal-500/30' : ''
        }`}
        style={{ borderLeftColor: ev.color }}
      >
        <div className="flex items-start gap-2">
          <span className="text-base" aria-hidden>
            📅
          </span>
          <div className="min-w-0 flex-1">
            <p className="font-medium text-zinc-100">{ev.title}</p>
            <p className="text-xs text-zinc-500">
              {ev.startTime}–{ev.endTime} · {ev.calendarName}
            </p>
          </div>
        </div>
      </article>
    )
  }

  if (entry.kind === 'chore') {
    const c = entry.chore
    const done = choreDoneOverride[c.id] ?? c.done
    return (
      <article className="rounded-xl border border-dashed border-zinc-700/80 bg-zinc-900/40 px-3 py-3 sm:px-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">🧹 Chore</p>
            <p className="mt-1 font-medium text-zinc-300">{c.name}</p>
            <span className="mt-1 inline-block rounded-full bg-[#1a1f2e] px-2 py-0.5 text-[10px] text-zinc-400">
              {c.frequency}
            </span>
            <span className="ml-2 text-lg" aria-label={done ? 'Done' : 'Pending'}>
              {done ? '✅' : '⏳'}
            </span>
          </div>
          <button
            type="button"
            onClick={() => onChoreDone(c.id)}
            className="min-h-[44px] shrink-0 rounded-lg border border-[#2a3142] px-3 text-sm text-zinc-300 hover:border-teal-500/40"
          >
            Mark done
          </button>
        </div>
      </article>
    )
  }

  if (entry.kind === 'habit-block') {
    const period = entry.period
    const set = period === 'morning' ? morningLogged : eveningLogged
    const allDone = entry.habits.every(
      (h) => set.has(h.id) || h.lastLogged === todayIso,
    )
    const pulse =
      eveningHighlight && period === 'evening' && !allDone ? 'evening-pulse rounded-xl' : ''

    return (
      <article
        className={`border border-[#1f2430] bg-[#12151c] px-3 py-3 sm:px-4 ${allDone ? 'opacity-50' : ''} ${pulse}`}
      >
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-500">
          {entry.label}
        </p>
        <ul className="mt-3 space-y-3">
          {entry.habits.map((h) => {
            const on = set.has(h.id) || h.lastLogged === todayIso
            return (
              <li key={h.id} className="flex items-center justify-between gap-3">
                <span className="text-sm text-zinc-200">
                  {h.emoji} {h.name}
                  <span className="ml-2 text-xs text-zinc-500">({h.streak} streak)</span>
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={on}
                  onClick={() => onToggleHabit(period, h.id)}
                  className={`relative h-9 w-14 shrink-0 rounded-full transition ${
                    on ? 'bg-teal-600' : 'bg-zinc-700'
                  }`}
                >
                  <span
                    className={`absolute top-1 h-7 w-7 rounded-full bg-white transition ${
                      on ? 'left-6' : 'left-1'
                    }`}
                  />
                </button>
              </li>
            )
          })}
        </ul>
      </article>
    )
  }

  if (entry.kind === 'tasks-block') {
    const overdue = entry.overdue.filter((t) => !taskDoneIds.has(t.id))
    const dueToday = entry.dueToday.filter((t) => !taskDoneIds.has(t.id))
    return (
      <article className="rounded-xl border border-[#1f2430] bg-[#0c0e12]/80 px-3 py-3 sm:px-4">
        {overdue.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] font-bold uppercase tracking-wide text-red-400">Overdue</p>
            <ul className="mt-2 space-y-2">
              {overdue.map((t) => (
                <li key={t.id} className="flex items-center gap-2 text-sm text-red-300">
                  <span className={`h-2 w-2 rounded-full ${priorityDot[t.priority]}`} />
                  <label className="flex flex-1 cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={taskDoneIds.has(t.id)}
                      onChange={() => onToggleTask(t.id)}
                      className="h-4 w-4 rounded border-zinc-600"
                    />
                    {t.title}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-[10px] font-bold uppercase tracking-wide text-zinc-500">Due today</p>
        {dueToday.length === 0 && overdue.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">All clear.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {dueToday.map((t) => (
              <li key={t.id} className="flex items-center gap-2 text-sm text-zinc-200">
                <span className={`h-2 w-2 rounded-full ${priorityDot[t.priority]}`} />
                <label className="flex flex-1 cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={taskDoneIds.has(t.id)}
                    onChange={() => onToggleTask(t.id)}
                    className="h-4 w-4 rounded border-zinc-600"
                  />
                  {t.title}
                </label>
              </li>
            ))}
          </ul>
        )}
      </article>
    )
  }

  if (entry.kind === 'reminder') {
    const r = entry.reminder
    return (
      <div className="flex items-start gap-2 py-1 text-sm text-zinc-400">
        <span aria-hidden>{r.icon}</span>
        <div>
          <p className="text-zinc-200">{r.text}</p>
          <p className="text-xs text-zinc-600">{r.when}</p>
        </div>
      </div>
    )
  }

  return null
}
