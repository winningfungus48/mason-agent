import { useEffect, useState } from 'react'
import { fetchReminders } from '../api/reminders'
import type { Reminder } from '../constants/mockData'

export function RemindersDetailView() {
  const [reminders, setReminders] = useState<Reminder[]>([])

  useEffect(() => {
    fetchReminders().then(setReminders)
  }, [])

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <ul className="mx-auto max-w-2xl space-y-3">
        {reminders.map((r) => (
          <li
            key={r.id}
            className="flex min-h-[56px] gap-3 rounded-2xl border border-[#1f2430] bg-[#12151c] p-4"
          >
            <span className="text-2xl" aria-hidden>
              {r.icon}
            </span>
            <div className="min-w-0">
              <p className="font-medium text-zinc-200">{r.text}</p>
              <p className="mt-1 text-xs text-zinc-500">{r.when}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
