/** Vite-inlined API base URL (no trailing slash). */
export function apiBase(): string {
  const base =
    (import.meta.env.VITE_API_URL as string | undefined) ??
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    ''
  return base.replace(/\/$/, '')
}

export function isApiConfigured(): boolean {
  return apiBase().length > 0
}

/**
 * ngrok free tier serves an interstitial HTML page (no CORS headers) unless this header is set.
 * Must be sent on every browser request to *.ngrok-free.dev / *.ngrok.io / *.ngrok.app.
 */
export function ngrokSkipHeaders(): Record<string, string> {
  const base = apiBase()
  if (!base) return {}
  try {
    const host = new URL(base).hostname
    if (
      host.endsWith('.ngrok-free.dev') ||
      host.endsWith('.ngrok.io') ||
      host.endsWith('.ngrok.app')
    ) {
      return { 'ngrok-skip-browser-warning': '69420' }
    }
  } catch {
    /* invalid URL */
  }
  return {}
}
