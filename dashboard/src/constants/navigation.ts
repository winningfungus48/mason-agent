/** Primary shell routes (bottom tabs + desktop nav). */
export type PrimaryView =
  | 'home'
  | 'calendar'
  | 'habits'
  | 'chores'
  | 'tasks'
  | 'chat'

/** Extra full-screen routes opened from Home (no bottom tab). */
export type StackView = 'brief' | 'grocery' | 'reminders'

export function isStackView(v: AppView): v is StackView {
  return v === 'brief' || v === 'grocery' || v === 'reminders'
}

export type AppView = PrimaryView | StackView

export function isPrimaryView(v: AppView): v is PrimaryView {
  return (
    v === 'home' ||
    v === 'calendar' ||
    v === 'habits' ||
    v === 'chores' ||
    v === 'tasks' ||
    v === 'chat'
  )
}
