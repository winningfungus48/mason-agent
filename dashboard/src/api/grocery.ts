import { GROCERY_CATEGORIES } from '../constants/mockData'
import type { GroceryItem } from '../constants/mockData'
import { apiJson } from './client'

export type GroceryResponse = {
  categories: readonly string[]
  byCategory: Record<string, GroceryItem[]>
}

export async function fetchGroceryList(): Promise<GroceryResponse> {
  const data = await apiJson<{ categories: Record<string, string[]>; total_items: number }>('/grocery')
  const keys = Object.keys(data.categories).filter((k) => (data.categories[k] ?? []).length > 0)
  const order = keys.sort((a, b) => {
    const ia = GROCERY_CATEGORIES.indexOf(a as (typeof GROCERY_CATEGORIES)[number])
    const ib = GROCERY_CATEGORIES.indexOf(b as (typeof GROCERY_CATEGORIES)[number])
    if (ia === -1 && ib === -1) return a.localeCompare(b)
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
  const byCategory: Record<string, GroceryItem[]> = {}
  for (const cat of order) {
    byCategory[cat] = (data.categories[cat] ?? []).map((label, i) => ({
      id: `${cat}-${i}-${label}`.slice(0, 64),
      label,
      checked: false,
    }))
  }
  return { categories: order, byCategory }
}

export async function addGroceryItem(item: string) {
  return apiJson<{ success: boolean; category: string; item: string; message?: string }>('/grocery/add', {
    method: 'POST',
    body: JSON.stringify({ item }),
  })
}

export async function removeGroceryItem(item: string) {
  return apiJson<{ success: boolean; message?: string }>('/grocery/remove', {
    method: 'POST',
    body: JSON.stringify({ item }),
  })
}
