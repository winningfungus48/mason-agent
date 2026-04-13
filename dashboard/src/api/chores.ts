import type { Chore } from '../constants/mockData'
import { apiJson } from './client'

type ChoreRow = {
  name: string
  frequency: string
  completed: boolean
  last_done: string | null
  days_since: number
}

function bucketFromFrequency(freq: string): Chore['bucket'] {
  const f = freq.toUpperCase()
  if (f.startsWith('DAILY')) return 'today'
  if (f.startsWith('WEEKLY')) return 'week'
  return 'month'
}

function mapRow(c: ChoreRow, id: string): Chore {
  return {
    id,
    name: c.name,
    frequency: c.frequency,
    done: c.completed,
    daysSinceLastDone: c.last_done != null ? c.days_since : null,
    bucket: bucketFromFrequency(c.frequency),
  }
}

/** Today's chore list (Command Center + quick status). */
export async function fetchTodaysChores(): Promise<Chore[]> {
  const data = await apiJson<{ chores: ChoreRow[] }>('/chores/today')
  return data.chores.map((c, i) => mapRow(c, `c${i + 1}`))
}

/** Full chore list for the Chores tab (all frequencies). */
export async function fetchChores(): Promise<Chore[]> {
  const data = await apiJson<{ chores: ChoreRow[] }>('/chores/status')
  return data.chores.map((c, i) => mapRow(c, `chore-${i}`))
}

export async function completeChore(choreName: string, note?: string): Promise<{ success: boolean; message: string }> {
  return apiJson<{ success: boolean; message: string }>('/chores/complete', {
    method: 'POST',
    body: JSON.stringify({ chore_name: choreName, note: note ?? null }),
  })
}
