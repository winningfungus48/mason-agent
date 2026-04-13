import { useNavigation } from '../../context/NavigationContext'

const titles: Record<string, string> = {
  brief: 'Morning brief',
  grocery: 'Grocery list',
  reminders: 'Reminders',
}

export function MobileStackHeader() {
  const { view, goBackFromStack } = useNavigation()

  if (view !== 'brief' && view !== 'grocery' && view !== 'reminders') return null

  return (
    <header className="sticky top-0 z-30 flex min-h-[48px] items-center gap-3 border-b border-[#1f2430] bg-[#0c0e12]/95 px-3 py-2 backdrop-blur-md lg:hidden">
      <button
        type="button"
        onClick={goBackFromStack}
        className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-xl text-lg text-zinc-300 hover:bg-[#12151c]"
        aria-label="Back to home"
      >
        ←
      </button>
      <h1 className="text-base font-semibold">{titles[view]}</h1>
    </header>
  )
}
