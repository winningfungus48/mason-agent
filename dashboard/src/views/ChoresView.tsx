import { useEffect, useMemo, useState } from 'react'
import { completeChore, fetchChores } from '../api/chores'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { Chore } from '../constants/mockData'

type Bucket = 'today' | 'week' | 'month'

const bucketLabel: Record<Bucket, string> = {
  today: 'Today',
  week: 'This Week',
  month: 'This Month',
}

function groupByFrequency(items: Chore[]) {
  const map = new Map<string, Chore[]>()
  for (const c of items) {
    const k = c.frequency
    if (!map.has(k)) map.set(k, [])
    map.get(k)!.push(c)
  }
  return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
}

export function ChoresView() {
  const [bucket, setBucket] = useState<Bucket>('today')
  const [chores, setChores] = useState<Chore[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function reload() {
    fetchChores()
      .then((c) => {
        setChores(c)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    reload()
  }, [])

  const filtered = useMemo(
    () => chores.filter((c) => c.bucket === bucket),
    [chores, bucket],
  )

  const grouped = useMemo(() => groupByFrequency(filtered), [filtered])

  async function logComplete(c: Chore) {
    if (!window.confirm(`Mark “${c.name}” as complete?`)) return
    const res = await completeChore(c.name)
    if (res.success) {
      reload()
    } else {
      window.alert(res.message)
    }
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={6} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load chores" />
      </div>
    )
  }

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <h1 className="text-xl font-semibold">Chores</h1>
      <p className="mt-1 text-sm text-zinc-500">Household rhythm</p>

      <div className="mx-auto mt-5 flex max-w-lg rounded-xl border border-[#1f2430] bg-[#0c0e12] p-1">
        {(['today', 'week', 'month'] as const).map((b) => (
          <button
            key={b}
            type="button"
            onClick={() => setBucket(b)}
            className={`min-h-[44px] flex-1 rounded-lg px-2 text-xs font-semibold sm:text-sm ${
              bucket === b
                ? 'bg-teal-600 text-white shadow'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {bucketLabel[b]}
          </button>
        ))}
      </div>

      <div className="mx-auto mt-6 max-w-2xl space-y-8">
        {grouped.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Nothing in this bucket.</p>
        ) : (
          grouped.map(([frequency, items]) => (
            <section key={frequency}>
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                {frequency}
              </h2>
              <ul className="space-y-3">
                {items.map((c) => (
                  <li
                    key={c.id}
                    className="rounded-2xl border border-[#1f2430] bg-[#12151c] p-4"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <p className="font-medium text-zinc-100">{c.name}</p>
                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-[#1a1f2e] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
                            {c.frequency}
                          </span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                              c.done
                                ? 'bg-emerald-500/15 text-emerald-400'
                                : 'bg-amber-500/10 text-amber-400'
                            }`}
                          >
                            {c.done ? '✅ Done' : '⏳ Pending'}
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-zinc-500">
                          {c.daysSinceLastDone === null
                            ? 'Never logged'
                            : c.daysSinceLastDone === 0
                              ? 'Last done today'
                              : `${c.daysSinceLastDone} days ago`}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => logComplete(c)}
                        className="min-h-[44px] shrink-0 rounded-xl border border-[#2a3142] bg-[#0c0e12] px-4 text-sm font-medium text-zinc-200 hover:border-teal-500/40 hover:text-teal-300"
                      >
                        Log complete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
    </div>
  )
}
