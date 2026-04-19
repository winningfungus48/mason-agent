/**
 * Static UI copy — edit `appContent.json` only; components import from here.
 * Vite bundles JSON at build time; no runtime fetch.
 */
import type { PrimaryView } from '../constants/navigation'
import raw from './appContent.json'

export type NavItem = {
  id: PrimaryView
  label: string
  icon: string
}

type AppContentShape = {
  shell: {
    eyebrow: string
    title: string
    subtitle: string
    chatLabel: string
    backToHome: string
    ariaBack: string
  }
  primaryNav: NavItem[]
  stackTitles: Record<string, string>
  calendar: {
    pageTitle: string
    today: string
    modes: { day: string; week: string; month: string }
    prevAria: string
    nextAria: string
    monthGridLabel: string
    eventsThisMonth: string
    noEvents: string
    noData: string
    loadError: string
  }
}

export const appContent = raw as AppContentShape

/** First five routes; Chat is separate in desktop layout. */
export function desktopMainNav(): NavItem[] {
  return appContent.primaryNav.filter((n) => n.id !== 'chat')
}

export function chatNavItem(): NavItem {
  const c = appContent.primaryNav.find((n) => n.id === 'chat')
  if (!c) throw new Error('appContent.json: missing chat nav item')
  return c
}
