import type { Habit } from '../constants/mockData'
import { todayIsoDate } from '../utils/date'
import { apiJson } from './client'

const HABIT_IDS: Record<string, string> = {
  workout: 'h1',
  water: 'h2',
  stretching: 'h3',
}

type HabitsTodayApi = {
  date: string
  habits: {
    name: string
    emoji: string
    completed: boolean | null
    note: string | null
    streak: number
  }[]
}

export async function fetchHabits(): Promise<Habit[]> {
  const data = await apiJson<HabitsTodayApi>('/habits/today')
  const today = todayIsoDate()
  return data.habits.map((h) => ({
    id: HABIT_IDS[h.name] ?? h.name,
    emoji: h.emoji,
    name: h.name.charAt(0).toUpperCase() + h.name.slice(1),
    streak: h.streak,
    lastLogged: h.completed === true ? today : 'never',
    weekDots: [false, false, false, false, false, false, false],
  }))
}
