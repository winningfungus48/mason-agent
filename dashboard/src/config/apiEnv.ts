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
