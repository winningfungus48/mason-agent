/** Horizontally scrollable life-area tabs (maps to mockTasksByList keys). */
export const TASK_LIFE_TABS = [
  { id: 'home', label: 'Home', listKey: 'Home' as const },
  { id: 'errands', label: 'Errands', listKey: 'Errands & Auto' as const },
  { id: 'finance', label: 'Finance', listKey: 'Finance' as const },
  { id: 'grocery', label: 'Grocery', listKey: 'Grocery & Essentials' as const },
  { id: 'buy', label: 'Buy List', listKey: 'Buy List' as const },
  { id: 'health', label: 'Health', listKey: 'Health & Fitness' as const },
  { id: 'ai', label: 'AI & Learning', listKey: 'AI & Learning' as const },
] as const
