import { isStackView } from '../../constants/navigation'
import { appContent } from '../../content/appContent'
import { useNavigation } from '../../context/NavigationContext'

export function DesktopStackBar() {
  const { view, goBackFromStack } = useNavigation()

  if (!isStackView(view)) return null

  return (
    <div className="sticky top-0 z-20 hidden border-b border-[#1f2430] bg-[#0c0e12]/95 px-6 py-2 backdrop-blur-md lg:flex lg:items-center">
      <button
        type="button"
        onClick={goBackFromStack}
        className="flex min-h-[44px] min-w-[44px] items-center gap-2 rounded-xl px-2 text-sm font-medium text-zinc-300 hover:bg-[#12151c]"
      >
        {appContent.shell.backToHome}
      </button>
    </div>
  )
}
