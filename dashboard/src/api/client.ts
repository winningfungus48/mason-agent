/**
 * Typed fetch helper for the Mason FastAPI backend.
 * Set `VITE_API_URL` and `VITE_API_KEY` in `.env.local` (gitignored).
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function apiBase(): string {
  const base =
    (import.meta.env.VITE_API_URL as string | undefined) ??
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    ''
  return base.replace(/\/$/, '')
}

export function apiKey(): string {
  return (import.meta.env.VITE_API_KEY as string | undefined) ?? ''
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const base = apiBase()
  if (!base) {
    throw new ApiError(0, 'VITE_API_URL is not set')
  }
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body != null) {
    headers.set('Content-Type', 'application/json')
  }
  headers.set('X-API-Key', apiKey())

  const res = await fetch(url, { ...init, headers })
  const text = await res.text()
  let body: unknown = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = { error: text || 'Invalid JSON from server' }
  }
  if (!res.ok) {
    const errObj = body as { error?: string }
    const msg = errObj?.error ?? res.statusText ?? 'Request failed'
    throw new ApiError(res.status, msg)
  }
  return body as T
}
