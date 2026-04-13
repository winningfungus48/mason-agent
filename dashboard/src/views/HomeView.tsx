import { useEffect, useMemo, useState } from 'react'
import { fetchCommandBriefCard } from '../api/briefing'
import { fetchTodayCalendar, fetchTomorrowPreviewBlock } from '../api/calendar'
import { fetchTodaysChores } from '../api/chores'
import { fetchHabits } from '../api/habits'
import { fetchTasksDueToday, fetchTasksDueTomorrow } from '../api/tasks'
import { AllDayBanner } from '../components/command-center/AllDayBanner'
import { DayHeader } from '../components/command-center/DayHeader'
import { MorningBriefCard } from '../components/command-center/MorningBriefCard'
import { QuickActionsRow } from '../components/command-center/QuickActionsRow'
import { Timeline } from '../components/command-center/Timeline'
import { TomorrowPreview } from '../components/command-center/TomorrowPreview'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import {
  mockTimelineReminders,
  type CommandBriefExpanded,
} from '../constants/commandCenterMock'
import type { CalendarEvent, Chore, Habit, TaskItem } from '../constants/mockData'
import { useCurrentTime } from '../hooks/useCurrentTime'
import { buildTimelineEntries } from '../lib/commandCenterTimeline'
import { todayIsoDate } from '../utils/date'

function sortEventsByTime(events: CalendarEvent[]) {
  return [...events].sort((a, b) => a.startTime.localeCompare(b.startTime))
}

const REFRESH_MS = 5 * 60 * 1000

export function HomeView() {
  const now = useCurrentTime()
  const todayIso = useMemo(() => todayIsoDate(), [])

  const hour = now.getHours()
  const nowMinutes = hour * 60 + now.getMinutes()
  const deEmphasizeBrief = hour >= 10
  const eveningHighlight = hour >= 18

  const dateLine = useMemo(
    () =>
      now.toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      }),
    [now],
  )

  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [allDayEvents, setAllDayEvents] = useState<{ id: string; title: string; color: string }[]>([])
  const [chores, setChores] = useState<Chore[]>([])
  const [habits, setHabits] = useState<Habit[]>([])
  const [allTasks, setAllTasks] = useState<TaskItem[]>([])
  const [brief, setBrief] = useState<CommandBriefExpanded | null>(null)
  const [tomorrowLabel, setTomorrowLabel] = useState('')
  const [tomorrowEvents, setTomorrowEvents] = useState<
    Pick<CalendarEvent, 'title' | 'startTime' | 'endTime' | 'color'>[]
  >([])
  const [tomorrowTasks, setTomorrowTasks] = useState<
    Pick<TaskItem, 'id' | 'title' | 'priority'>[]
  >([])

  const [loading, setLoading] = useState(true)
  const [errCalendar, setErrCalendar] = useState<string | null>(null)
  const [errChores, setErrChores] = useState<string | null>(null)
  const [errHabits, setErrHabits] = useState<string | null>(null)
  const [errTasks, setErrTasks] = useState<string | null>(null)
  const [errBrief, setErrBrief] = useState<string | null>(null)
  const [errTomorrow, setErrTomorrow] = useState<string | null>(null)

  const [morningLogged, setMorningLogged] = useState<Set<string>>(() => new Set())
  const [eveningLogged, setEveningLogged] = useState<Set<string>>(() => new Set())
  const [choreDone, setChoreDone] = useState<Record<string, boolean>>({})
  const [taskDoneIds, setTaskDoneIds] = useState<Set<string>>(() => new Set())

  useEffect(() => {
    let cancelled = false

    async function loadCommandCenter() {
      setLoading(true)
      const results = await Promise.allSettled([
        fetchTodayCalendar(),
        fetchTodaysChores(),
        fetchHabits(),
        fetchTasksDueToday(),
        fetchCommandBriefCard(),
        fetchTomorrowPreviewBlock(),
        fetchTasksDueTomorrow(),
      ])
      if (cancelled) return

      const [rCal, rChores, rHabits, rTasks, rBrief, rTom, rTomTasks] = results

      if (rCal.status === 'fulfilled') {
        setEvents(sortEventsByTime(rCal.value.events))
        setAllDayEvents(rCal.value.allDayEvents)
        setErrCalendar(null)
      } else {
        setErrCalendar(rCal.reason instanceof Error ? rCal.reason.message : 'Failed')
      }

      if (rChores.status === 'fulfilled') {
        setChores(rChores.value)
        setErrChores(null)
      } else {
        setErrChores(rChores.reason instanceof Error ? rChores.reason.message : 'Failed')
      }

      if (rHabits.status === 'fulfilled') {
        setHabits(rHabits.value)
        setErrHabits(null)
      } else {
        setErrHabits(rHabits.reason instanceof Error ? rHabits.reason.message : 'Failed')
      }

      if (rTasks.status === 'fulfilled') {
        setAllTasks(rTasks.value)
        setErrTasks(null)
      } else {
        setErrTasks(rTasks.reason instanceof Error ? rTasks.reason.message : 'Failed')
      }

      if (rBrief.status === 'fulfilled') {
        setBrief(rBrief.value)
        setErrBrief(rBrief.value ? null : 'No brief cached yet')
      } else {
        setBrief(null)
        setErrBrief(rBrief.reason instanceof Error ? rBrief.reason.message : 'Failed')
      }

      if (rTom.status === 'fulfilled') {
        setTomorrowLabel(rTom.value.dateLabel)
        setTomorrowEvents(rTom.value.events)
        setErrTomorrow(null)
      } else {
        setErrTomorrow(rTom.reason instanceof Error ? rTom.reason.message : 'Failed')
      }

      if (rTomTasks.status === 'fulfilled') {
        setTomorrowTasks(rTomTasks.value)
      }

      setLoading(false)
    }

    loadCommandCenter()
    const id = window.setInterval(loadCommandCenter, REFRESH_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  const nextEvent = events[0] ?? null

  const timelineEntries = useMemo(
    () =>
      buildTimelineEntries(
        events,
        chores,
        habits,
        allTasks,
        mockTimelineReminders,
        todayIso,
      ),
    [events, chores, habits, allTasks, todayIso],
  )

  const summaryLine = useMemo(() => {
    const nTask = allTasks.length
    const nChore = chores.filter((c) => !c.done).length
    const nHabit = habits.filter((h) => h.lastLogged !== todayIso).length
    return `${nTask} tasks due · ${nChore} chores open · ${nHabit} habits to log`
  }, [allTasks, chores, habits, todayIso])

  const habitNames = habits.map((h) => ({
    id: h.id,
    label: `${h.emoji} ${h.name}`,
  }))

  const habitLoggedQuick = useMemo(() => {
    const o: Record<string, boolean> = {}
    for (const h of habits) {
      o[h.id] = morningLogged.has(h.id) || h.lastLogged === todayIso
    }
    return o
  }, [habits, morningLogged, todayIso])

  function onQuickLogHabit(id: string, logged: boolean) {
    setMorningLogged((prev) => {
      const n = new Set(prev)
      if (logged) n.add(id)
      else n.delete(id)
      return n
    })
  }

  function onToggleHabit(period: 'morning' | 'evening', habitId: string) {
    const setter = period === 'morning' ? setMorningLogged : setEveningLogged
    setter((prev) => {
      const n = new Set(prev)
      if (n.has(habitId)) n.delete(habitId)
      else n.add(habitId)
      return n
    })
  }

  function onChoreDone(id: string) {
    setChoreDone((prev) => ({ ...prev, [id]: true }))
  }

  function onToggleTask(id: string) {
    setTaskDoneIds((prev) => {
      const n = new Set(prev)
      if (n.has(id)) n.delete(id)
      else n.add(id)
      return n
    })
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="sticky top-0 z-40 border-b border-[#1f2430] bg-[#0c0e12]/95 backdrop-blur-md">
        <DayHeader dateLine={dateLine} summaryLine={summaryLine} />
        <QuickActionsRow
          nextEvent={nextEvent}
          habitNames={habitNames}
          habitLoggedState={habitLoggedQuick}
          onLogHabit={onQuickLogHabit}
        />
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 px-0 pb-6 pt-3 lg:grid lg:grid-cols-5 lg:gap-6 lg:px-8 lg:pb-10">
        <div className="min-h-0 space-y-4 lg:col-span-3 lg:flex lg:flex-col lg:gap-4">
          <div className="px-4 lg:hidden">
            {loading ? (
              <SectionSkeleton rows={4} />
            ) : errBrief || !brief ? (
              <LoadErrorCard label={errBrief ?? 'Unable to load morning brief'} />
            ) : (
              <MorningBriefCard
                brief={brief}
                deEmphasize={deEmphasizeBrief}
                variant="mobile"
              />
            )}
          </div>

          <div className="px-4 lg:px-0">
            {loading ? (
              <SectionSkeleton rows={2} />
            ) : errCalendar ? (
              <LoadErrorCard label="Unable to load calendar" />
            ) : (
              <AllDayBanner events={allDayEvents} />
            )}
          </div>

          <div className="min-h-0 flex-1 px-2 sm:px-4 lg:px-0">
            <h2 className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500 lg:px-0">
              Today
            </h2>
            {loading ? (
              <SectionSkeleton rows={6} />
            ) : errCalendar && errChores && errHabits && errTasks ? (
              <LoadErrorCard label="Unable to load timeline" />
            ) : (
              <Timeline
                entries={timelineEntries}
                nowMinutes={nowMinutes}
                todayIso={todayIso}
                morningLogged={morningLogged}
                eveningLogged={eveningLogged}
                onToggleHabit={onToggleHabit}
                choreDoneOverride={choreDone}
                onChoreDone={onChoreDone}
                taskDoneIds={taskDoneIds}
                onToggleTask={onToggleTask}
                eveningHighlight={eveningHighlight}
              />
            )}
          </div>

          <div className="px-4 lg:hidden">
            {loading ? (
              <SectionSkeleton rows={3} />
            ) : errTomorrow ? (
              <LoadErrorCard label="Unable to load tomorrow" />
            ) : (
              <TomorrowPreview
                dateLabel={tomorrowLabel}
                events={tomorrowEvents}
                tasks={tomorrowTasks}
              />
            )}
          </div>
        </div>

        <aside className="hidden min-h-0 flex-col gap-4 lg:col-span-2 lg:flex">
          {loading ? (
            <SectionSkeleton rows={4} />
          ) : errBrief || !brief ? (
            <LoadErrorCard label={errBrief ?? 'Unable to load morning brief'} />
          ) : (
            <MorningBriefCard
              brief={brief}
              deEmphasize={deEmphasizeBrief}
              variant="desktop"
            />
          )}
          {loading ? (
            <SectionSkeleton rows={3} />
          ) : errTomorrow ? (
            <LoadErrorCard label="Unable to load tomorrow" />
          ) : (
            <TomorrowPreview
              dateLabel={tomorrowLabel}
              events={tomorrowEvents}
              tasks={tomorrowTasks}
            />
          )}
        </aside>
      </div>
    </div>
  )
}
