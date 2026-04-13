import { isStackView } from '../../constants/navigation'
import type { PrimaryView } from '../../constants/navigation'
import { useChat } from '../../context/ChatContext'
import { useNavigation } from '../../context/NavigationContext'

const items: { id: PrimaryView; label: string; icon: string }[] = [
  { id: 'home', label: 'Home', icon: '🏠' },
  { id: 'calendar', label: 'Calendar', icon: '📅' },
  { id: 'habits', label: 'Habits', icon: '💪' },
  { id: 'chores', label: 'Chores', icon: '🧹' },
  { id: 'tasks', label: 'Tasks', icon: '✅' },
]

export function DesktopSidebar() {
  const { view, goToPrimary } = useNavigation()
  const { setDesktopOpen } = useChat()

  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r border-[#1f2430] bg-[#0c0e12] lg:flex lg:sticky lg:top-0 lg:h-screen lg:self-start">
      <div className="border-b border-[#1f2430] px-4 py-5">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-400/90">
          Personal ops
        </p>
        <h1 className="mt-1 text-lg font-semibold tracking-tight">Chief of Staff</h1>
        <p className="mt-1 text-xs text-zinc-500">Local skeleton · mock data</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Desktop navigation">
        {items.map((item) => {
          const active =
            item.id === 'home' ? view === 'home' || isStackView(view) : view === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => goToPrimary(item.id)}
              className={`flex min-h-[44px] w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium transition ${
                active
                  ? 'bg-teal-500/15 text-teal-300'
                  : 'text-zinc-400 hover:bg-[#12151c] hover:text-zinc-200'
              }`}
            >
              <span className="text-lg" aria-hidden>
                {item.icon}
              </span>
              {item.label}
            </button>
          )
        })}
        <button
          type="button"
          onClick={() => setDesktopOpen(true)}
          className="mt-auto flex min-h-[44px] w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium text-zinc-400 transition hover:bg-[#12151c] hover:text-teal-300"
        >
          <span className="text-lg" aria-hidden>
            💬
          </span>
          Chat
        </button>
      </nav>
    </aside>
  )
}
