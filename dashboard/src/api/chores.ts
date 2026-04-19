import type { Chore } from '../constants/mockData'
import { ApiError, apiJson } from './client'

export type ChoreApiRow = {
  id: string
  name: string
  category: string
  emoji: string
  completed: boolean
  last_done: string | null
  days_since: number | null
  schedule?: 'weekly' | 'monthly'
  due_label?: string
  overdue?: boolean
}

export type ChoresTodayResponse = {
  date: string
  day: string
  day_label: string
  day_emoji: string
  chores: ChoreApiRow[]
  summary: { total: number; completed: number; pending: number }
  message: string | null
}

export type WeekDayBlock = {
  label: string
  emoji: string
  chores: ChoreApiRow[]
  summary: { total: number; completed: number; pending: number }
  all_done: boolean
}

export type ChoresWeekResponse = {
  days: Record<string, WeekDayBlock>
}

export type ChoresMonthlyResponse = {
  label: string
  emoji: string
  chores: ChoreApiRow[]
  summary: { total: number; completed: number; pending: number }
}

export type ChoresQuarterlyResponse = {
  label: string
  emoji: string
  quarter_start: string
  quarter_label: string
  chores: ChoreApiRow[]
  summary: { total: number; completed: number; pending: number }
}

export type ChoresAllResponse = {
  date: string
  today: ChoresTodayResponse
  week: ChoresWeekResponse
  monthly: ChoresMonthlyResponse
  quarterly: ChoresQuarterlyResponse
}

/** Command Center + home summary — maps API to shared `Chore` shape. */
export async function fetchTodaysChores(): Promise<Chore[]> {
  const data = await apiJson<ChoresTodayResponse>('/chores/today')
  return data.chores.map((c) => ({
    id: c.id,
    name: c.name,
    frequency: c.schedule === 'monthly' ? 'Monthly' : 'Weekly',
    done: c.completed,
    daysSinceLastDone: c.days_since ?? null,
    bucket: 'today',
    category: c.category,
    emoji: c.emoji,
  }))
}

export async function fetchChoresToday(): Promise<ChoresTodayResponse> {
  return apiJson<ChoresTodayResponse>('/chores/today')
}

export async function fetchChoresAll(): Promise<ChoresAllResponse> {
  return apiJson<ChoresAllResponse>('/chores/all')
}

/**
 * Prefer `/chores/all` (one round-trip). If that returns 404 (proxy or older deploy),
 * compose the same payload from the individual endpoints — avoids a single missing route
 * breaking the whole tab.
 */
export async function fetchChoresBundle(): Promise<ChoresAllResponse> {
  try {
    return await fetchChoresAll()
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      const [today, week, monthly, quarterly] = await Promise.all([
        apiJson<ChoresTodayResponse>('/chores/today'),
        apiJson<ChoresWeekResponse>('/chores/week'),
        apiJson<ChoresMonthlyResponse>('/chores/monthly'),
        apiJson<ChoresQuarterlyResponse>('/chores/quarterly'),
      ])
      return {
        date: today.date,
        today,
        week,
        monthly,
        quarterly,
      }
    }
    throw e
  }
}

export async function completeChore(
  choreId: string,
  choreName: string,
  note?: string,
): Promise<{ success: boolean; message: string }> {
  return apiJson<{ success: boolean; message: string }>('/chores/complete', {
    method: 'POST',
    body: JSON.stringify({
      chore_id: choreId,
      chore_name: choreName,
      note: note ?? null,
    }),
  })
}
