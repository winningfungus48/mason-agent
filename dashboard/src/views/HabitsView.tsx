import { useEffect, useState } from 'react'
import { fetchHabits } from '../api/habits'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { Habit } from '../constants/mockData'
import { mondayIndex, todayIsoDate } from '../utils/date'

type Period = 'morning' | 'evening'

const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'] as const

function WeekDots({ habit }: { habit: Habit }) {
  const today = new Date()
  const idxToday = mondayIndex(today)

  return (
    <div className="mt-3 flex items-center gap-2">
      <span className="text-[10px] uppercase tracking-wider text-zinc-600">This week</span>
      <div className="flex gap-1.5">
        {dayLabels.map((label, i) => {
          const isFuture = i > idxToday
          const dot = habit.weekDots[i]
          return (
            <div key={`${habit.id}-${label}-${i}`} className="flex flex-col items-center gap-0.5">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  isFuture
                    ? 'bg-zinc-800/80 ring-1 ring-zinc-700/50'
                    : dot
                      ? 'bg-teal-500'
                      : 'bg-transparent ring-2 ring-zinc-600'
                }`}
                title={isFuture ? 'Future' : dot ? 'Done' : 'Missed'}
              />
              <span className="text-[9px] text-zinc-600">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function HabitsView() {
  const [period, setPeriod] = useState<Period>('morning')
  const [habits, setHabits] = useState<Habit[]>([])
  const [loggedToday, setLoggedToday] = useState<Set<string>>(() => new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const today = todayIsoDate()

  useEffect(() => {
    let cancelled = false
    fetchHabits()
      .then((h) => {
        if (cancelled) return
        setHabits(h)
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

  function toggleHabit(id: string) {
    setLoggedToday((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={5} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load habits" />
      </div>
    )
  }

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <h1 className="text-xl font-semibold lg:text-lg">Habits</h1>
      <p className="mt-1 text-sm text-zinc-500">
        {period === 'morning' ? 'Morning rhythm' : 'Evening check-out'}
      </p>

      <div className="mx-auto mt-5 flex max-w-md rounded-full border border-[#1f2430] bg-[#0c0e12] p-1">
        {(['morning', 'evening'] as const).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPeriod(p)}
            className={`min-h-[44px] flex-1 rounded-full px-4 text-sm font-medium transition ${
              period === p ? 'bg-teal-600 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {p === 'morning' ? 'Morning' : 'Evening'}
          </button>
        ))}
      </div>

      <ul className="mt-8 space-y-4">
        {habits.map((habit) => (
          <li
            key={habit.id}
            className="rounded-2xl border border-[#1f2430] bg-[#12151c] p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-zinc-100">
                  {habit.emoji} {habit.name}
                </p>
                <p className="mt-1 text-sm text-zinc-500">Streak: {habit.streak} days</p>
                <WeekDots habit={habit} />
              </div>
              <button
                type="button"
                onClick={() => toggleHabit(habit.id)}
                className={`min-h-[44px] rounded-xl px-4 text-sm font-medium ${
                  loggedToday.has(habit.id) || habit.lastLogged === today
                    ? 'bg-teal-600/20 text-teal-300'
                    : 'border border-[#2a3142] bg-[#0c0e12] text-zinc-300'
                }`}
              >
                {loggedToday.has(habit.id) || habit.lastLogged === today ? 'Logged' : 'Log'}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
