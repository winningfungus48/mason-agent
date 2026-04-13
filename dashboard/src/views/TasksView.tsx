import { useEffect, useMemo, useState } from 'react'
import { completeTask, fetchTasksByList } from '../api/tasks'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { TaskItem } from '../constants/mockData'
import { TASK_LIFE_TABS } from '../constants/taskTabs'
import { todayIsoDate } from '../utils/date'

const priorityDot = {
  high: 'bg-red-500',
  medium: 'bg-amber-400',
  low: 'bg-zinc-500',
} as const

export function TasksView() {
  const [tasksByList, setTasksByList] = useState<Record<string, TaskItem[]>>({})
  const [tabId, setTabId] = useState<(typeof TASK_LIFE_TABS)[number]['id']>('home')
  const [completedIds, setCompletedIds] = useState<Set<string>>(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const today = useMemo(() => todayIsoDate(), [])

  useEffect(() => {
    let cancelled = false
    fetchTasksByList()
      .then((res) => {
        if (cancelled) return
        setTasksByList(res.tasksByList)
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

  const activeListKey = TASK_LIFE_TABS.find((t) => t.id === tabId)?.listKey ?? 'Home'
  const tasks = tasksByList[activeListKey] ?? []

  async function toggleComplete(taskId: string) {
    const task = tasks.find((t) => t.id === taskId)
    const willComplete = !completedIds.has(taskId)
    if (task && willComplete) {
      await completeTask(task.title, activeListKey)
    }
    setCompletedIds((prev) => {
      const next = new Set(prev)
      if (next.has(taskId)) next.delete(taskId)
      else next.add(taskId)
      return next
    })
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

  if (error) {
    return (
      <div className="flex min-h-0 flex-1 flex-col px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load tasks" />
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col pt-4 lg:pt-6">
      <div className="px-4 sm:px-6 lg:px-8">
        <h1 className="text-xl font-semibold">Tasks</h1>
        <p className="mt-1 text-sm text-zinc-500">Life-area lists</p>
      </div>

      <div className="mt-4 w-full overflow-x-auto border-b border-[#1f2430] pb-px">
        <div className="flex min-h-[48px] w-max gap-1 px-4 sm:px-6 lg:px-8">
          {TASK_LIFE_TABS.map((t) => {
            const active = tabId === t.id
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTabId(t.id)}
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

      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-8 pt-4 sm:px-6 lg:px-8">
        {tasks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#2a3142] py-16 text-center text-sm text-zinc-500">
            All done in this list.
          </div>
        ) : (
          <ul className="mx-auto max-w-2xl space-y-2">
            {tasks.map((t) => {
              const done = completedIds.has(t.id)
              const overdue = t.dueDate < today && !done
              return (
                <li
                  key={t.id}
                  className={`flex min-h-[52px] items-center gap-3 rounded-2xl border border-[#1f2430] bg-[#12151c] px-3 py-2 ${
                    overdue ? 'border-red-500/35 bg-red-500/5' : ''
                  }`}
                >
                  <span
                    className={`h-2.5 w-2.5 shrink-0 rounded-full ${priorityDot[t.priority]}`}
                    title="Priority"
                  />
                  <label className="flex min-h-[44px] min-w-0 flex-1 cursor-pointer items-center gap-3">
                    <input
                      type="checkbox"
                      checked={done}
                      onChange={() => toggleComplete(t.id)}
                      className="h-5 w-5 shrink-0 rounded border-[#2a3142] bg-[#0c0e12] text-teal-500"
                    />
                    <span
                      className={`min-w-0 flex-1 text-sm ${
                        done ? 'text-zinc-500 line-through' : overdue ? 'text-red-300' : 'text-zinc-100'
                      }`}
                    >
                      {t.title}
                    </span>
                  </label>
                  <span
                    className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-medium ${
                      overdue ? 'bg-red-500/20 text-red-300' : 'bg-[#1a1f2e] text-zinc-400'
                    }`}
                  >
                    {t.dueDate}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
