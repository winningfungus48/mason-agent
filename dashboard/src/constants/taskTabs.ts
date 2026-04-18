/**
 * listKey must match Google Tasks list titles (emoji prefixes where used by tasks_setup_lists).
 * Inbox = default list titled "Main List" in Google Tasks.
 */
export const TASK_LIFE_TABS = [
  { id: 'inbox', label: 'Inbox', listKey: 'Main List' as const },
  { id: 'home', label: 'Home', listKey: '🏠 Home' as const },
  { id: 'errands', label: 'Errands', listKey: '🚗 Errands & Auto' as const },
  { id: 'finance', label: 'Finance', listKey: '💰 Finance' as const },
  { id: 'grocery', label: 'Grocery', listKey: '🛒 Grocery & Essentials' as const },
  { id: 'buy', label: 'Buy List', listKey: '🛍️ Buy List' as const },
  { id: 'health', label: 'Health', listKey: '💪 Health & Fitness' as const },
  { id: 'ai', label: 'AI & Learning', listKey: '🤖 AI & Learning' as const },
] as const
