import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import type { AppView, PrimaryView, StackView } from '../constants/navigation'
import { isPrimaryView } from '../constants/navigation'

type NavigationContextValue = {
  view: AppView
  setView: (v: AppView) => void
  primaryTab: PrimaryView
  goToPrimary: (p: PrimaryView) => void
  openStack: (v: StackView) => void
  goBackFromStack: () => void
}

const NavigationContext = createContext<NavigationContextValue | null>(null)

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [view, setViewState] = useState<AppView>('home')

  const primaryTab: PrimaryView = isPrimaryView(view)
    ? view
    : 'home'

  const setView = useCallback((v: AppView) => {
    setViewState(v)
  }, [])

  const goToPrimary = useCallback((p: PrimaryView) => {
    setViewState(p)
  }, [])

  const openStack = useCallback((v: StackView) => {
    setViewState(v)
  }, [])

  const goBackFromStack = useCallback(() => {
    setViewState('home')
  }, [])

  const value = useMemo(
    () => ({
      view,
      setView,
      primaryTab,
      goToPrimary,
      openStack,
      goBackFromStack,
    }),
    [view, setView, primaryTab, goToPrimary, openStack, goBackFromStack],
  )

  return (
    <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>
  )
}

export function useNavigation() {
  const ctx = useContext(NavigationContext)
  if (!ctx) throw new Error('useNavigation must be used within NavigationProvider')
  return ctx
}
