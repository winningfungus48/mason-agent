import { type FormEvent, useEffect, useState } from 'react'
import { addGroceryItem, fetchGroceryList } from '../api/grocery'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { GroceryItem } from '../constants/mockData'

export function GroceryDetailView() {
  const [categories, setCategories] = useState<string[]>([])
  const [byCategory, setByCategory] = useState<Record<string, GroceryItem[]>>({})
  const [newItem, setNewItem] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)

  function load() {
    return fetchGroceryList()
      .then((res) => {
        setCategories([...res.categories])
        setByCategory(res.byCategory)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  function toggleItem(cat: string, id: string) {
    setByCategory((prev) => ({
      ...prev,
      [cat]: (prev[cat] ?? []).map((g) =>
        g.id === id ? { ...g, checked: !g.checked } : g,
      ),
    }))
  }

  async function addItem(e: FormEvent) {
    e.preventDefault()
    const label = newItem.trim()
    if (!label) return
    setAdding(true)
    try {
      await addGroceryItem(label)
      setNewItem('')
      await load()
    } catch (err) {
      window.alert(err instanceof Error ? err.message : 'Could not add item')
    } finally {
      setAdding(false)
    }
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={8} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load grocery list" />
      </div>
    )
  }

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <div className="space-y-6">
        {categories.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Your grocery list is empty.</p>
        ) : (
          categories.map((cat) => {
            const items = byCategory[cat] ?? []
            return (
              <section key={cat}>
                <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  {cat}
                </h2>
                <ul className="space-y-1">
                  {items.map((item) => (
                    <li key={item.id}>
                      <label className="flex min-h-[44px] cursor-pointer items-center gap-3 rounded-xl px-2 py-2 hover:bg-[#12151c]">
                        <input
                          type="checkbox"
                          checked={item.checked}
                          onChange={() => toggleItem(cat, item.id)}
                          className="h-5 w-5 rounded border-[#2a3142] bg-[#0c0e12] text-teal-500"
                        />
                        <span
                          className={`text-sm ${item.checked ? 'text-zinc-600 line-through' : 'text-zinc-200'}`}
                        >
                          {item.label}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              </section>
            )
          })
        )}
      </div>

      <form onSubmit={addItem} className="mt-8 flex gap-2 border-t border-[#1f2430] pt-4">
        <input
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="Add item"
          className="min-h-[44px] min-w-0 flex-1 rounded-xl border border-[#1f2430] bg-[#0c0e12] px-3 py-2 text-sm text-zinc-100 outline-none focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20"
        />
        <button
          type="submit"
          disabled={adding}
          className="min-h-[44px] shrink-0 rounded-xl bg-teal-600 px-5 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50"
        >
          Add
        </button>
      </form>
    </div>
  )
}
