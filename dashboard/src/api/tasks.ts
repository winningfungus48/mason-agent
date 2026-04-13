import { TASK_LIFE_TABS } from '../constants/taskTabs'
import type { TaskItem } from '../constants/mockData'
import { todayIsoDate, tomorrowIsoDate } from '../utils/date'
import { apiJson } from './client'

export type TasksByListResponse = {
  order: readonly string[]
  tasksByList: Record<string, TaskItem[]>
}

type ApiTask = {
  title: string
  list: string
  due: string
  priority: string
}

function slugId(list: string, title: string, i: number) {
  return `${list}-${i}-${title}`.replace(/\s+/g, '-').toLowerCase().slice(0, 80)
}

function mapApiTask(t: ApiTask, list: string, i: number): TaskItem {
  const due =
    t.due === '—' || !t.due ? todayIsoDate() : t.due.slice(0, 10)
  return {
    id: slugId(list, t.title, i),
    title: t.title,
    dueDate: due,
    priority: t.priority as TaskItem['priority'],
    listName: list,
  }
}

export async function fetchTasksByList(): Promise<TasksByListResponse> {
  const keys = TASK_LIFE_TABS.map((t) => t.listKey)
  const results = await Promise.all(
    keys.map((listKey) =>
      apiJson<{ tasks: ApiTask[] }>(`/tasks/list/${encodeURIComponent(listKey)}`).catch(() => ({
        tasks: [] as ApiTask[],
      })),
    ),
  )
  const tasksByList: Record<string, TaskItem[]> = {}
  keys.forEach((k, i) => {
    tasksByList[k] = results[i].tasks.map((t, j) => mapApiTask(t, k, j))
  })
  return { order: keys, tasksByList }
}

/** Tasks due today (Command Center). */
export async function fetchTasksDueToday(): Promise<TaskItem[]> {
  const data = await apiJson<{ tasks: ApiTask[] }>('/tasks/today')
  return data.tasks.map((t, i) => mapApiTask(t, t.list, i))
}

type WeekApi = { days: Record<string, ApiTask[]> }

export async function fetchTasksDueTomorrow(): Promise<Pick<TaskItem, 'id' | 'title' | 'priority'>[]> {
  const data = await apiJson<WeekApi>('/tasks/week')
  const key = tomorrowIsoDate()
  const row = data.days[key] ?? []
  return row.map((t, i) => ({
    id: slugId(t.list, t.title, i),
    title: t.title,
    priority: t.priority as TaskItem['priority'],
  }))
}

export async function completeTask(title: string, listName?: string): Promise<boolean> {
  const res = await apiJson<{ success: boolean }>('/tasks/complete', {
    method: 'POST',
    body: JSON.stringify({ title, list_name: listName ?? null }),
  })
  return res.success
}
