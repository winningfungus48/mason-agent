import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  completeChore,
  fetchChoresBundle,
  type ChoreApiRow,
  type ChoresAllResponse,
} from '../api/chores'
import { isApiConfigured } from '../config/apiEnv'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'

const REFRESH_MS = 5 * 60 * 1000

const CATEGORY_HEX: Record<string, string> = {
  'Kitchen & Cooking': '#F97316',
  Bathrooms: '#3B82F6',
  'Floors & Surfaces': '#8B5CF6',
  Laundry: '#14B8A6',
  'Outdoor & Yard': '#22C55E',
  Pets: '#EAB308',
  'Home Maintenance': '#EF4444',
}

const SCHEDULED_WEEK_DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'] as const
const RIBBON_ORDER = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'] as const

function categoryStyle(category: string): { background: string; color: string } {
  const hex = CATEGORY_HEX[category] ?? '#71717a'
  return { background: `${hex}22`, color: hex }
}

type ViewScope = 'day' | 'week'

function groupByCategory(
  chores: ChoreApiRow[],
  isDone: (c: ChoreApiRow) => boolean,
): [string, ChoreApiRow[]][] {
  const m = new Map<string, ChoreApiRow[]>()
  for (const c of chores) {
    if (!m.has(c.category)) m.set(c.category, [])
    m.get(c.category)!.push(c)
  }
  for (const arr of m.values()) {
    arr.sort((a, b) => {
      const da = isDone(a) ? 1 : 0
      const db = isDone(b) ? 1 : 0
      if (da !== db) return da - db
      return a.name.localeCompare(b.name)
    })
  }
  return Array.from(m.entries()).sort(([a], [b]) => a.localeCompare(b))
}

/** Week Sun–Sat containing anchorIso (YYYY-MM-DD). */
function ribbonCells(anchorIso: string): { key: string; date: Date }[] {
  const anchor = new Date(anchorIso + 'T12:00:00')
  const sun = new Date(anchor)
  sun.setDate(anchor.getDate() - anchor.getDay())
  return RIBBON_ORDER.map((key, i) => {
    const d = new Date(sun)
    d.setDate(sun.getDate() + i)
    return { key, date: d }
  })
}

function ChoreCheckbox({
  checked,
  busy,
  onToggle,
}: {
  checked: boolean
  busy: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      disabled={busy || checked}
      onClick={onToggle}
      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border-2 transition motion-safe:duration-200 ${
        checked
          ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
          : 'border-[#2a3142] bg-[#0c0e12] text-zinc-500 hover:border-teal-500/50 hover:text-teal-300'
      } ${busy ? 'opacity-60' : ''}`}
      aria-label={checked ? 'Completed' : 'Mark complete'}
    >
      {checked ? <span className="text-xl">✓</span> : <span className="text-lg"> </span>}
    </button>
  )
}

function ChoreCard({
  c,
  done,
  subtitle,
  busyId,
  dueLabel,
  overdue,
  onComplete,
}: {
  c: ChoreApiRow
  done: boolean
  subtitle: string
  busyId: string | null
  dueLabel?: string
  overdue?: boolean
  onComplete: (c: ChoreApiRow) => void
}) {
  const cs = categoryStyle(c.category)
  const ring = overdue ? 'ring-1 ring-amber-500/50' : ''
  return (
    <li
      className={`rounded-2xl border border-[#1f2430] bg-[#12151c] p-3 sm:p-4 ${ring} ${
        done ? 'opacity-75' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-lg"
          style={{ background: cs.background, color: cs.color }}
        >
          {c.emoji}
        </div>
        <div className="min-w-0 flex-1">
          <p className={`font-medium text-zinc-100 ${done ? 'line-through' : ''}`}>{c.name}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ background: cs.background, color: cs.color }}
            >
              {c.category}
            </span>
            {dueLabel ? (
              <span className="text-[10px] font-medium text-zinc-500">{dueLabel}</span>
            ) : null}
          </div>
          <p className="mt-1 text-xs text-zinc-500">{subtitle}</p>
        </div>
        <ChoreCheckbox checked={done} busy={busyId === c.id} onToggle={() => onComplete(c)} />
      </div>
    </li>
  )
}

function choreSubtitle(c: ChoreApiRow, done: boolean): string {
  if (done) return 'Done this period'
  if (c.days_since === null || c.last_done === null) return 'Never logged'
  if (c.days_since === 0) return 'Last done today'
  if (c.days_since === 1) return '1 day ago'
  return `${c.days_since} days ago`
}

export function ChoresView() {
  const needsApiEnv = !isApiConfigured()
  const [all, setAll] = useState<ChoresAllResponse | null>(null)
  const [loading, setLoading] = useState(() => isApiConfigured())
  const [error, setError] = useState<string | null>(null)
  const [viewScope, setViewScope] = useState<ViewScope>('day')
  const [selectedDay, setSelectedDay] = useState<string | null>(null)
  const [optimistic, setOptimistic] = useState<Set<string>>(() => new Set())
  const [busyId, setBusyId] = useState<string | null>(null)
  const [flashId, setFlashId] = useState<string | null>(null)

  const isDone = useCallback(
    (c: ChoreApiRow) => c.completed || optimistic.has(c.id),
    [optimistic],
  )

  const reload = useCallback(async () => {
    const data = await fetchChoresBundle()
    setAll(data)
    setSelectedDay((prev) => prev ?? data.today.day)
    setOptimistic(new Set())
  }, [])

  useEffect(() => {
    if (!isApiConfigured()) return
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        await reload()
        if (!cancelled) setError(null)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [reload])

  useEffect(() => {
    if (!isApiConfigured()) return
    const id = window.setInterval(() => {
      reload().catch(() => {})
    }, REFRESH_MS)
    return () => window.clearInterval(id)
  }, [reload])

  const todayData = all?.today
  const weekDays = all?.week.days
  const monthly = all?.monthly
  const quarterly = all?.quarterly

  const onComplete = useCallback(
    async (c: ChoreApiRow) => {
      if (isDone(c)) return
      setOptimistic((prev) => new Set(prev).add(c.id))
      setBusyId(c.id)
      try {
        const res = await completeChore(c.id, c.name)
        if (!res.success) throw new Error(res.message)
        setFlashId(c.id)
        window.setTimeout(() => setFlashId(null), 600)
        await reload()
      } catch (e) {
        setOptimistic((prev) => {
          const n = new Set(prev)
          n.delete(c.id)
          return n
        })
        window.alert(e instanceof Error ? e.message : 'Could not log chore')
      } finally {
        setBusyId(null)
      }
    },
    [isDone, reload],
  )

  const displayedChores = useMemo(() => {
    if (!all) return []
    const dk = selectedDay ?? all.today.day
    if (dk === all.today.day) {
      return all.today.chores
    }
    const block = all.week.days[dk]
    return block?.chores ?? []
  }, [all, selectedDay])

  const dayMessage = useMemo(() => {
    if (!all) return null
    const dk = selectedDay ?? all.today.day
    if (dk === 'friday' || dk === 'saturday') {
      return 'No chores scheduled — enjoy your day off 🎉'
    }
    if (dk === all.today.day && all.today.message) {
      return all.today.message
    }
    return null
  }, [all, selectedDay])

  const daySummary = useMemo(() => {
    const total = displayedChores.length
    const completed = displayedChores.filter((c) => isDone(c)).length
    return { total, completed, pending: total - completed }
  }, [displayedChores, isDone])

  const todayGrouped = useMemo(() => {
    return groupByCategory(displayedChores, isDone)
  }, [displayedChores, isDone])

  const progressRatio =
    daySummary.total > 0 ? daySummary.completed / daySummary.total : 0

  const ribbon = useMemo(() => {
    if (!all?.date) return []
    return ribbonCells(all.date)
  }, [all?.date])

  const dayHeaderTitle = useMemo(() => {
    if (!all) return ''
    const dk = selectedDay ?? all.today.day
    const short = dk.charAt(0).toUpperCase() + dk.slice(1)
    if (dk === 'friday' || dk === 'saturday') {
      return short
    }
    const block = weekDays?.[dk]
    const theme = block?.label && block?.emoji ? `${block.label} ${block.emoji}` : ''
    return theme ? `${short} — ${theme}` : short
  }, [selectedDay, all, weekDays])

  if (needsApiEnv) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <h1 className="text-xl font-semibold text-zinc-100">Chores</h1>
        <p className="mt-1 text-sm text-zinc-500">Household rhythm</p>
        <div className="mx-auto mt-6 max-w-2xl rounded-2xl border border-amber-500/25 bg-[#12151c] px-4 py-5 text-sm text-zinc-300">
          <p className="font-semibold text-amber-200/95">Connect the dashboard to your API</p>
          <p className="mt-2 leading-relaxed text-zinc-400">
            Create{' '}
            <code className="rounded bg-[#0c0e12] px-1.5 py-0.5 text-xs text-zinc-300">dashboard/.env.local</code>{' '}
            with <code className="text-xs text-zinc-400">VITE_API_URL=...</code> and restart the dev server. Sign in
            with your dashboard password, or set <code className="text-xs text-zinc-400">VITE_API_KEY</code> for
            automation.
          </p>
        </div>
      </div>
    )
  }

  if (loading && !all) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={6} />
      </div>
    )
  }

  if (error || !all || !todayData) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <h1 className="text-xl font-semibold text-zinc-100">Chores</h1>
        <p className="mt-1 text-sm text-zinc-500">Household rhythm</p>
        <div className="mx-auto mt-6 max-w-2xl space-y-3">
          <LoadErrorCard label="Unable to load chores" />
          {error ? (
            <p className="rounded-xl border border-[#2a3142] bg-[#0c0e12] px-3 py-2 text-left text-xs leading-relaxed text-zinc-400">
              {error}
            </p>
          ) : null}
          <p className="text-xs text-zinc-600">
            If you see “Not Found”, the API may be missing chore routes — deploy the latest <code className="text-zinc-500">api.py</code> and{' '}
            <code className="text-zinc-500">documents/chores.json</code>, restart mason-api, and confirm{' '}
            <code className="text-zinc-500">GET /chores/today</code> works with your auth header.
          </p>
        </div>
      </div>
    )
  }

  const isoToday = all.date
  const apiTodayDay = todayData.day
  const dayKey = selectedDay ?? apiTodayDay

  function CalendarRibbon() {
    return (
      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-max gap-1.5 sm:gap-2">
          {ribbon.map(({ key, date }) => {
            const isSel = dayKey === key
            const isCalToday =
              date.getFullYear() === new Date(isoToday + 'T12:00:00').getFullYear() &&
              date.getMonth() === new Date(isoToday + 'T12:00:00').getMonth() &&
              date.getDate() === new Date(isoToday + 'T12:00:00').getDate()
            const wd = date.toLocaleDateString(undefined, { weekday: 'short' })
            const dm = date.getDate()
            return (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedDay(key)}
                className={`flex min-w-[3.25rem] flex-col items-center rounded-xl border px-2 py-2 text-center transition sm:min-w-[3.75rem] sm:px-3 ${
                  isSel
                    ? 'border-teal-500/70 bg-teal-600/20 text-teal-100'
                    : 'border-[#1f2430] bg-[#12151c] text-zinc-400 hover:border-zinc-600'
                } ${isCalToday && !isSel ? 'ring-1 ring-teal-500/40' : ''}`}
              >
                <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">{wd}</span>
                <span className="text-lg font-semibold text-zinc-100">{dm}</span>
                {weekDays?.[key]?.emoji ? (
                  <span className="mt-0.5 text-sm" aria-hidden>
                    {weekDays[key].emoji}
                  </span>
                ) : key === 'friday' || key === 'saturday' ? (
                  <span className="mt-0.5 text-[10px] text-zinc-600">Off</span>
                ) : null}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  function renderDayView() {
    return (
      <section className="space-y-4">
        <header className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Selected day</p>
          <h2 className="text-lg font-semibold text-zinc-100">{dayHeaderTitle}</h2>
          {dayMessage ? (
            <p className="text-sm text-zinc-400">{dayMessage}</p>
          ) : (
            <>
              <div className="h-2 overflow-hidden rounded-full bg-[#1a1f2e]">
                <div
                  className="h-full rounded-full bg-teal-500 transition-[width] motion-safe:duration-500"
                  style={{ width: `${Math.round(progressRatio * 100)}%` }}
                />
              </div>
              <p className="text-xs text-zinc-500">
                {daySummary.completed}/{daySummary.total} done
                {dayKey === apiTodayDay ? ' · Today' : ''}
              </p>
            </>
          )}
        </header>

        {dayMessage && displayedChores.length === 0 ? null : displayedChores.length === 0 && !dayMessage ? (
          <p className="text-center text-sm text-zinc-500">Nothing scheduled for this day.</p>
        ) : daySummary.total > 0 && daySummary.pending === 0 && !dayMessage ? (
          <p className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 py-8 text-center text-emerald-200">
            All done! 🎉
          </p>
        ) : (
          <ul className="space-y-6">
            {todayGrouped.map(([cat, items]) => (
              <li key={cat}>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{cat}</p>
                <ul className="space-y-3">
                  {items.map((c) => (
                    <ChoreCard
                      key={c.id}
                      c={c}
                      done={isDone(c)}
                      subtitle={choreSubtitle(c, isDone(c))}
                      busyId={busyId}
                      onComplete={onComplete}
                    />
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    )
  }

  function renderWeekOverview() {
    if (!weekDays) return null
    return (
      <section className="space-y-4">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">This week at a glance</p>
        <div className="space-y-4">
          {SCHEDULED_WEEK_DAYS.map((dk) => {
            const block = weekDays[dk]
            if (!block) return null
            const doneDay = block.summary.total > 0 && block.summary.pending === 0
            return (
              <div key={dk} className="rounded-2xl border border-[#1f2430] bg-[#12151c] p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="text-lg">{block.emoji}</span>
                  <h3 className="font-semibold text-zinc-100">
                    {dk.charAt(0).toUpperCase() + dk.slice(1)}
                    {block.label ? ` — ${block.label}` : ''}
                  </h3>
                  <span className="rounded-full bg-[#1a1f2e] px-2 py-0.5 text-[10px] font-semibold text-zinc-400">
                    {block.summary.completed}/{block.summary.total}
                  </span>
                  {doneDay ? <span className="text-emerald-400">✅</span> : null}
                </div>
                <ul className="space-y-2">
                  {block.chores.map((c) => (
                    <ChoreCard
                      key={c.id}
                      c={c}
                      done={isDone(c)}
                      subtitle={choreSubtitle(c, isDone(c))}
                      busyId={busyId}
                      onComplete={onComplete}
                    />
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      </section>
    )
  }

  const scopeToggle = (
    <div className="flex max-w-md rounded-xl border border-[#1f2430] bg-[#0c0e12] p-1">
      {(['day', 'week'] as const).map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => setViewScope(s)}
          className={`min-h-[44px] flex-1 rounded-lg px-3 text-sm font-semibold ${
            viewScope === s ? 'bg-teal-600 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {s === 'day' ? 'Day' : 'Week'}
        </button>
      ))}
    </div>
  )

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <h1 className="text-xl font-semibold text-zinc-100">Chores</h1>
      <p className="mt-1 text-sm text-zinc-500">Household rhythm</p>

      <div className="mx-auto mt-5 max-w-4xl space-y-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          {scopeToggle}
          <p className="text-xs text-zinc-500">
            Week of{' '}
            <span className="font-medium text-zinc-400">
              {ribbon[0]?.date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} —{' '}
              {ribbon[6]?.date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </span>
          </p>
        </div>

        <div className="rounded-2xl border border-[#1f2430] bg-[#0c0e12]/80 p-3 sm:p-4">
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Calendar</p>
          <CalendarRibbon />
        </div>

        {viewScope === 'day' ? renderDayView() : renderWeekOverview()}

        <details className="rounded-2xl border border-[#1f2430] bg-[#12151c] px-4 py-3">
          <summary className="cursor-pointer text-sm font-semibold text-zinc-300">
            Monthly & quarterly
          </summary>
          <div className="mt-4 space-y-8 border-t border-[#1f2430] pt-4">
            {monthly ? (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-zinc-300">
                  {monthly.emoji} {monthly.label}
                </h3>
                <ul className="space-y-6">
                  {groupByCategory(monthly.chores, isDone).map(([cat, items]) => (
                    <li key={cat}>
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{cat}</p>
                      <ul className="space-y-3">
                        {items.map((c) => (
                          <ChoreCard
                            key={c.id}
                            c={c}
                            done={isDone(c)}
                            subtitle={choreSubtitle(c, isDone(c))}
                            busyId={busyId}
                            dueLabel={c.due_label}
                            onComplete={onComplete}
                          />
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {quarterly ? (
              <div>
                <h3 className="mb-1 text-sm font-semibold text-zinc-300">
                  {quarterly.emoji} {quarterly.label}
                </h3>
                <p className="mb-3 text-xs text-zinc-500">{quarterly.quarter_label}</p>
                <ul className="space-y-6">
                  {groupByCategory(quarterly.chores, isDone).map(([cat, items]) => (
                    <li key={cat}>
                      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{cat}</p>
                      <ul className="space-y-3">
                        {items.map((c) => (
                          <ChoreCard
                            key={c.id}
                            c={c}
                            done={isDone(c)}
                            subtitle={choreSubtitle(c, isDone(c))}
                            busyId={busyId}
                            overdue={c.overdue === true}
                            onComplete={onComplete}
                          />
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </details>
      </div>

      {flashId ? (
        <span className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-lg">
          Logged ✓
        </span>
      ) : null}
    </div>
  )
}
