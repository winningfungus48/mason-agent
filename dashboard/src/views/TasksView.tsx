import { useEffect, useState } from 'react'
import { completeTask, fetchTasksByList, reopenTask } from '../api/tasks'
import { ConnectGoogleBanner } from '../components/ConnectGoogleBanner'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { TaskItem } from '../constants/mockData'
import { TASK_LIFE_TABS } from '../constants/taskTabs'

const priorityDot = {
  high: 'bg-red-500',
  medium: 'bg-amber-400',
  low: 'bg-zinc-500',
} as const

type TabId = (typeof TASK_LIFE_TABS)[number]['id']

export function TasksView() {
  const [tasksByList, setTasksByList] = useState<Record<string, TaskItem[]>>({})
  /** Session-only: tasks completed in this visit (cleared on reload). */
  const [completedByList, setCompletedByList] = useState<Record<string, TaskItem[]>>({})
  const [tabId, setTabId] = useState<TabId>('inbox')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionErr, setActionErr] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const res = await fetchTasksByList()
        if (cancelled) return
        setTasksByList(res.tasksByList)
        setCompletedByList({})
        setError(null)
      } catch (e) {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Unable to load tasks')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const activeListKey =
    TASK_LIFE_TABS.find((t) => t.id === tabId)?.listKey ?? TASK_LIFE_TABS[0].listKey
  const openTasks = tasksByList[activeListKey] ?? []
  const completedTasks = completedByList[activeListKey] ?? []

  async function markComplete(task: TaskItem) {
    setActionErr(null)
    try {
      const ok = await completeTask(task.title, activeListKey)
      if (!ok) {
        setActionErr('Could not complete task.')
        return
      }
      setTasksByList((prev) => ({
        ...prev,
        [activeListKey]: (prev[activeListKey] ?? []).filter((t) => t.id !== task.id),
      }))
      setCompletedByList((prev) => ({
        ...prev,
        [activeListKey]: [...(prev[activeListKey] ?? []), task],
      }))
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : 'Could not complete task.')
    }
  }

  async function markReopen(task: TaskItem) {
    setActionErr(null)
    try {
      const ok = await reopenTask(task.title, activeListKey)
      if (!ok) {
        setActionErr('Could not reopen task.')
        return
      }
      setCompletedByList((prev) => ({
        ...prev,
        [activeListKey]: (prev[activeListKey] ?? []).filter((t) => t.id !== task.id),
      }))
      setTasksByList((prev) => ({
        ...prev,
        [activeListKey]: [task, ...(prev[activeListKey] ?? [])],
      }))
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : 'Could not reopen task.')
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-0 flex-1 flex-col pt-4 lg:pt-6">
        <div className="px-4 sm:px-6 lg:px-8">
          <SectionSkeleton rows={6} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col pt-4 lg:pt-6">
      <div className="space-y-4 px-4 sm:px-6 lg:px-8">
        <ConnectGoogleBanner />
        <div>
          <h1 className="text-xl font-semibold">Tasks</h1>
          <p className="mt-1 text-sm text-zinc-500">Google Tasks — life-area lists</p>
        </div>
      </div>

      {error ? (
        <div className="mt-4 px-4 sm:px-6 lg:px-8">
          <LoadErrorCard label="Unable to load tasks" />
        </div>
      ) : (
        <>
          <div className="px-4 sm:px-6 lg:px-8">
            <h2 className="mt-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Google Tasks
            </h2>
          </div>

          <div className="mt-4 w-full overflow-x-auto border-b border-[#1f2430] pb-px">
            <div className="flex min-h-[48px] w-max gap-1 px-4 sm:px-6 lg:px-8">
              {TASK_LIFE_TABS.map((t) => {
                const active = tabId === t.id
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => {
                      setTabId(t.id)
                      setActionErr(null)
                    }}
                    className={`shrink-0 rounded-t-lg px-4 py-2 text-sm font-medium transition ${
                      active
                        ? 'bg-[#12151c] text-teal-300'
                        : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    {t.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 pb-8 pt-4 sm:px-6 lg:px-8">
            {actionErr ? (
              <p className="mb-3 text-center text-sm text-red-400" role="alert">
                {actionErr}
              </p>
            ) : null}

            {openTasks.length === 0 && completedTasks.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#2a3142] py-16 text-center text-sm text-zinc-500">
                All done in this list.
              </div>
            ) : openTasks.length === 0 ? (
              <p className="py-6 text-center text-sm text-zinc-500">No open tasks</p>
            ) : (
              <ul className="mx-auto max-w-2xl space-y-2">
                {openTasks.map((t) => (
                  <li
                    key={t.id}
                    className="flex min-h-[52px] items-center gap-3 rounded-2xl border border-[#1f2430] bg-[#12151c] px-3 py-2"
                  >
                    <span
                      className={`h-2.5 w-2.5 shrink-0 rounded-full ${priorityDot[t.priority]}`}
                      title="Priority"
                    />
                    <label className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-center gap-3">
                      <input
                        type="checkbox"
                        checked={false}
                        onChange={() => markComplete(t)}
                        className="h-5 w-5 shrink-0 rounded border-[#2a3142] bg-[#0c0e12] text-teal-500"
                      />
                      <span className="min-w-0 flex-1 text-sm text-zinc-100">{t.title}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )}

            {completedTasks.length > 0 ? (
              <details
                key={activeListKey}
                className="mx-auto mt-8 max-w-2xl border-t border-[#1f2430] pt-4"
              >
                <summary className="cursor-pointer list-none text-sm font-medium text-zinc-400 [&::-webkit-details-marker]:hidden">
                  <span className="inline-flex items-center gap-2">
                    <span className="text-zinc-500">▸</span>
                    Completed ({completedTasks.length})
                  </span>
                </summary>
                <ul className="mt-3 space-y-2">
                  {completedTasks.map((t) => (
                    <li
                      key={t.id}
                      className="flex min-h-[52px] items-center gap-3 rounded-2xl border border-[#1f2430]/80 bg-[#0c0e12]/80 px-3 py-2 opacity-90"
                    >
                      <span
                        className={`h-2.5 w-2.5 shrink-0 rounded-full ${priorityDot[t.priority]}`}
                        title="Priority"
                      />
                      <label className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-center gap-3">
                        <input
                          type="checkbox"
                          checked
                          onChange={() => markReopen(t)}
                          className="h-5 w-5 shrink-0 rounded border-[#2a3142] bg-[#0c0e12] text-teal-500"
                        />
                        <span className="min-w-0 flex-1 text-sm text-zinc-500 line-through">{t.title}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </div>
        </>
      )}
    </div>
  )
}
