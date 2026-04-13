import { useNavigation } from '../../context/NavigationContext'
import type { PrimaryView } from '../../constants/navigation'

const tabs: { id: PrimaryView; label: string; icon: string }[] = [
  { id: 'home', label: 'Home', icon: '🏠' },
  { id: 'calendar', label: 'Calendar', icon: '📅' },
  { id: 'habits', label: 'Habits', icon: '💪' },
  { id: 'chores', label: 'Chores', icon: '🧹' },
  { id: 'tasks', label: 'Tasks', icon: '✅' },
  { id: 'chat', label: 'Chat', icon: '💬' },
]

export function MobileTabBar() {
  const { primaryTab, goToPrimary } = useNavigation()

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#1f2430] bg-[#0c0e12]/95 backdrop-blur-md lg:hidden"
      style={{ paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom, 0px))' }}
      aria-label="Primary navigation"
    >
      <ul className="mx-auto flex max-w-lg items-stretch justify-between gap-0 px-1 pt-1">
        {tabs.map((t) => {
          const active = primaryTab === t.id
          return (
            <li key={t.id} className="min-w-0 flex-1">
              <button
                type="button"
                onClick={() => goToPrimary(t.id)}
                className={`flex min-h-[44px] w-full flex-col items-center justify-center gap-0.5 rounded-lg px-1 py-1 text-[10px] font-medium transition ${
                  active
                    ? 'text-teal-400'
                    : 'text-zinc-500 active:bg-[#12151c] active:text-zinc-300'
                }`}
              >
                <span className="text-lg leading-none" aria-hidden>
                  {t.icon}
                </span>
                <span className="truncate">{t.label}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
