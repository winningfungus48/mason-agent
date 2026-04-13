import type { ReactNode } from 'react'
import { DesktopChatDock } from './DesktopChatDock'
import { DesktopSidebar } from './DesktopSidebar'
import { MobileTabBar } from './MobileTabBar'

const TABBAR_PAD = 'pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))]'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-[#0c0e12] text-zinc-100 lg:flex-row">
      <DesktopSidebar />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <main
          className={`flex min-h-0 flex-1 flex-col ${TABBAR_PAD} lg:pb-6`}
        >
          {children}
        </main>
      </div>

      <MobileTabBar />
      <DesktopChatDock />
    </div>
  )
}
