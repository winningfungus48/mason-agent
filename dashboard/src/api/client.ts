/**
 * Typed fetch helper for the Mason FastAPI backend.
 * Set `VITE_API_URL` in `.env.development` / `.env.local`.
 * Auth: Bearer token from POST /auth/login (sessionStorage), or optional `VITE_API_KEY`.
 */
import { apiBase, ngrokSkipHeaders } from '../config/apiEnv'
import { getAccessToken } from './auth'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export { apiBase } from '../config/apiEnv'

export function apiKey(): string {
  return (import.meta.env.VITE_API_KEY as string | undefined) ?? ''
}

export { isApiConfigured } from '../config/apiEnv'

/** Per-request timeout so a hung connection cannot leave the UI loading forever. */
const DEFAULT_TIMEOUT_MS = 90_000

export async function apiJson<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const base = apiBase()
  if (!base) {
    throw new ApiError(0, 'VITE_API_URL is not set')
  }
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`
  const headers = new Headers(init.headers)
  for (const [k, v] of Object.entries(ngrokSkipHeaders())) {
    if (!headers.has(k)) headers.set(k, v)
  }
  if (!headers.has('Content-Type') && init.body != null) {
    headers.set('Content-Type', 'application/json')
  }
  const bearer = getAccessToken()
  const keyFallback = apiKey()
  if (bearer) {
    headers.set('Authorization', `Bearer ${bearer}`)
  } else if (keyFallback.trim()) {
    headers.set('X-API-Key', keyFallback)
  } else {
    throw new ApiError(0, 'Not signed in — unlock the dashboard or set VITE_API_KEY for automation')
  }

  const controller = new AbortController()
  const t = window.setTimeout(() => controller.abort(), timeoutMs)
  if (init.signal) {
    if (init.signal.aborted) controller.abort()
    else init.signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  let res: Response
  try {
    res = await fetch(url, { ...init, headers, signal: controller.signal })
  } catch (e: unknown) {
    const aborted =
      (e instanceof Error && e.name === 'AbortError') ||
      (typeof DOMException !== 'undefined' &&
        e instanceof DOMException &&
        e.name === 'AbortError')
    if (aborted) {
      throw new ApiError(
        0,
        `Request timed out after ${timeoutMs / 1000}s — check the API URL, port 8000 firewall, and that mason-api is running on the droplet.`,
      )
    }
    const msg = e instanceof Error ? e.message : String(e)
    if (
      e instanceof TypeError ||
      msg.includes('Failed to fetch') ||
      msg.includes('NetworkError') ||
      msg.includes('Load failed')
    ) {
      throw new ApiError(
        0,
        `Cannot reach the API at ${base}. If you use localhost for the dashboard, either run uvicorn here (e.g. port 8000) or set VITE_API_URL in dashboard/.env.local to your droplet HTTPS URL and restart npm run dev.`,
      )
    }
    throw e
  } finally {
    window.clearTimeout(t)
  }
  const text = await res.text()
  let body: unknown = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = { error: text || 'Invalid JSON from server' }
  }
  if (!res.ok) {
    const msg = messageFromErrorBody(body, res.statusText)
    throw new ApiError(res.status, msg)
  }
  return body as T
}

/** FastAPI uses `detail`; some routes use `error`. */
function messageFromErrorBody(body: unknown, statusText: string): string {
  if (!body || typeof body !== 'object') {
    return statusText || 'Request failed'
  }
  const o = body as Record<string, unknown>
  if (typeof o.error === 'string') return o.error
  if (typeof o.detail === 'string') return o.detail
  if (Array.isArray(o.detail) && o.detail.length > 0) {
    const first = o.detail[0]
    if (first && typeof first === 'object') {
      const row = first as Record<string, unknown>
      if (typeof row.msg === 'string') return row.msg
    }
  }
  if (o.detail && typeof o.detail === 'object' && !Array.isArray(o.detail)) {
    const d = o.detail as Record<string, unknown>
    if (typeof d.error === 'string') return d.error
  }
  return statusText || 'Request failed'
}
