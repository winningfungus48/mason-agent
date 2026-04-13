import { useState } from 'react'
import type { CalendarEvent } from '../../constants/mockData'
import { BottomSheet } from '../ui/BottomSheet'
import { useNavigation } from '../../context/NavigationContext'

const actions = [
  { id: 'log-habit' as const, icon: '✅', label: 'Log Habit' },
  { id: 'chore' as const, icon: '🧹', label: 'Done a Chore' },
  { id: 'grocery' as const, icon: '🛒', label: 'Add to Grocery' },
  { id: 'task' as const, icon: '☑️', label: 'Add Task' },
  { id: 'next' as const, icon: '📅', label: "What's Next" },
  { id: 'agent' as const, icon: '💬', label: 'Ask Agent' },
]

type Sheet = (typeof actions)[number]['id'] | null

type QuickActionsRowProps = {
  /** Next timed event for “What’s Next” modal. */
  nextEvent: CalendarEvent | null
  habitNames: { id: string; label: string }[]
  onLogHabit: (habitId: string, logged: boolean) => void
  habitLoggedState: Record<string, boolean>
}

export function QuickActionsRow({
  nextEvent,
  habitNames,
  onLogHabit,
  habitLoggedState,
}: QuickActionsRowProps) {
  const [sheet, setSheet] = useState<Sheet>(null)
  const { goToPrimary } = useNavigation()
  const [choreText, setChoreText] = useState('')
  const [groceryText, setGroceryText] = useState('')
  const [taskName, setTaskName] = useState('')
  const [taskDue, setTaskDue] = useState('')

  function close() {
    setSheet(null)
  }

  function open(s: Sheet) {
    setSheet(s)
  }

  function runAgent() {
    close()
    goToPrimary('chat')
  }

  return (
    <>
      <div className="border-b border-[#1f2430] bg-[#0c0e12]/95 px-3 pb-3 pt-1 backdrop-blur-md">
        <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wide text-zinc-600">
          Quick actions
        </p>
        <div className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:flex-wrap lg:overflow-visible">
          {actions.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => (a.id === 'agent' ? runAgent() : open(a.id))}
              className="flex min-h-[44px] shrink-0 items-center gap-2 rounded-full border border-[#1f2430] bg-[#12151c] px-4 py-2 text-sm font-medium text-zinc-300 transition hover:border-teal-500/40 hover:text-teal-200"
            >
              <span aria-hidden>{a.icon}</span>
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <BottomSheet
        open={sheet === 'log-habit'}
        onClose={close}
        title="Log habit"
      >
        <ul className="space-y-3">
          {habitNames.map((h) => (
            <li key={h.id} className="flex items-center justify-between gap-3 rounded-xl border border-[#1f2430] px-3 py-2">
              <span className="text-sm text-zinc-200">{h.label}</span>
              <button
                type="button"
                onClick={() => onLogHabit(h.id, !habitLoggedState[h.id])}
                className={`min-h-[44px] rounded-lg px-4 text-sm font-medium ${
                  habitLoggedState[h.id]
                    ? 'bg-teal-600 text-white'
                    : 'border border-zinc-600 text-zinc-300'
                }`}
              >
                {habitLoggedState[h.id] ? 'Logged' : 'Log'}
              </button>
            </li>
          ))}
        </ul>
      </BottomSheet>

      <BottomSheet open={sheet === 'chore'} onClose={close} title="Done a chore">
        <label className="block text-xs text-zinc-500">Which chore?</label>
        <input
          value={choreText}
          onChange={(e) => setChoreText(e.target.value)}
          className="mt-2 min-h-[44px] w-full rounded-xl border border-[#1f2430] bg-[#0c0e12] px-3 text-sm text-zinc-100"
          placeholder="e.g. Take out trash"
        />
        <button
          type="button"
          className="mt-4 min-h-[44px] w-full rounded-xl bg-teal-600 text-sm font-medium text-white"
          onClick={close}
        >
          Send (mock)
        </button>
      </BottomSheet>

      <BottomSheet open={sheet === 'grocery'} onClose={close} title="Add to grocery">
        <label className="block text-xs text-zinc-500">What item?</label>
        <input
          value={groceryText}
          onChange={(e) => setGroceryText(e.target.value)}
          className="mt-2 min-h-[44px] w-full rounded-xl border border-[#1f2430] bg-[#0c0e12] px-3 text-sm text-zinc-100"
        />
        <button
          type="button"
          className="mt-4 min-h-[44px] w-full rounded-xl bg-teal-600 text-sm font-medium text-white"
          onClick={close}
        >
          Send (mock)
        </button>
      </BottomSheet>

      <BottomSheet open={sheet === 'task'} onClose={close} title="Add task">
        <label className="block text-xs text-zinc-500">Task name</label>
        <input
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          className="mt-2 min-h-[44px] w-full rounded-xl border border-[#1f2430] bg-[#0c0e12] px-3 text-sm text-zinc-100"
        />
        <label className="mt-3 block text-xs text-zinc-500">Due date (optional)</label>
        <input
          type="date"
          value={taskDue}
          onChange={(e) => setTaskDue(e.target.value)}
          className="mt-2 min-h-[44px] w-full rounded-xl border border-[#1f2430] bg-[#0c0e12] px-3 text-sm text-zinc-100"
        />
        <button
          type="button"
          className="mt-4 min-h-[44px] w-full rounded-xl bg-teal-600 text-sm font-medium text-white"
          onClick={close}
        >
          Send (mock)
        </button>
      </BottomSheet>

      <BottomSheet open={sheet === 'next'} onClose={close} title="What's next">
        {nextEvent ? (
          <div className="rounded-xl border border-[#1f2430] bg-[#0c0e12] p-4">
            <p className="font-medium text-zinc-100">{nextEvent.title}</p>
            <p className="mt-1 text-sm text-zinc-500">
              {nextEvent.startTime}–{nextEvent.endTime} · {nextEvent.calendarName}
            </p>
            <div
              className="mt-2 h-1 w-12 rounded-full"
              style={{ backgroundColor: nextEvent.color }}
            />
          </div>
        ) : (
          <p className="text-sm text-zinc-500">No more timed events today.</p>
        )}
      </BottomSheet>
    </>
  )
}
