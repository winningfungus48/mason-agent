import { useMemo, useState } from 'react'
import {
  CHORES_BY_DAY,
  WEEKDAY_LABELS,
  WEEKDAY_ORDER,
  type WeekdayKey,
} from '../constants/choresStatic'

const DAY_THEME: Partial<Record<WeekdayKey, string>> = {
  monday: 'Laundry/Pets/Vacuum',
  tuesday: 'Rooms/Admin',
  wednesday: 'Bathrooms',
  thursday: 'Kitchen',
  friday: 'Surface',
  saturday: 'Outdoors',
}

function todaysDay(): WeekdayKey {
  const day = new Date().getDay()
  const map: WeekdayKey[] = [
    'sunday',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
  ]
  return map[day]
}

function choreId(day: WeekdayKey, label: string, index: number): string {
  return `${day}-${index}-${label}`.toLowerCase()
}

export function ChoresView() {
  const [selectedDay, setSelectedDay] = useState<WeekdayKey>(() => todaysDay())
  const [checkedByDay, setCheckedByDay] = useState<Record<WeekdayKey, Set<string>>>(() => ({
    monday: new Set(),
    tuesday: new Set(),
    wednesday: new Set(),
    thursday: new Set(),
    friday: new Set(),
    saturday: new Set(),
    sunday: new Set(),
  }))

  const chores = CHORES_BY_DAY[selectedDay]
  const checked = checkedByDay[selectedDay]
  const theme = DAY_THEME[selectedDay]

  const summary = useMemo(() => {
    const total = chores.length
    const done = checked.size
    return { total, done }
  }, [chores, checked])

  function toggleChore(id: string) {
    setCheckedByDay((prev) => {
      const next = new Set(prev[selectedDay])
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return { ...prev, [selectedDay]: next }
    })
  }

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <h1 className="text-xl font-semibold text-zinc-100">Chores</h1>
      <p className="mt-1 text-sm text-zinc-500">Daily checklist</p>

      <div className="mx-auto mt-5 max-w-4xl space-y-5">
        <div className="rounded-2xl border border-[#1f2430] bg-[#0c0e12]/80 p-3 sm:p-4">
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Days</p>
          <div className="grid grid-cols-7 gap-2">
            {WEEKDAY_ORDER.map((day) => {
              const isSelected = selectedDay === day
              return (
                <button
                  key={day}
                  type="button"
                  onClick={() => setSelectedDay(day)}
                  className={`min-h-[44px] rounded-xl border px-2 py-2 text-sm font-semibold transition ${
                    isSelected
                      ? 'border-teal-500/70 bg-teal-600/20 text-teal-100'
                      : 'border-[#1f2430] bg-[#12151c] text-zinc-400 hover:border-zinc-600'
                  }`}
                >
                  {WEEKDAY_LABELS[day]}
                </button>
              )
            })}
          </div>
        </div>

        <section className="space-y-3">
          {theme ? <p className="text-sm text-zinc-400">{theme}</p> : null}
          <p className="text-xs text-zinc-500">
            {summary.done}/{summary.total} done
          </p>
          <ul className="space-y-3">
            {chores.map((label, index) => {
              const id = choreId(selectedDay, label, index)
              const isDone = checked.has(id)
              return (
                <li
                  key={id}
                  className="rounded-2xl border border-[#1f2430] bg-[#12151c] px-4 py-3"
                >
                  <label className="flex cursor-pointer items-start gap-3">
                    <input
                      type="checkbox"
                      checked={isDone}
                      onChange={() => toggleChore(id)}
                      className="mt-0.5 h-4 w-4 rounded border-[#2a3142] bg-[#0c0e12] accent-teal-500"
                    />
                    <span
                      className={`text-sm ${isDone ? 'text-zinc-500 line-through' : 'text-zinc-200'}`}
                    >
                      {label}
                    </span>
                  </label>
                </li>
              )
            })}
          </ul>
        </section>
      </div>
    </div>
  )
}
