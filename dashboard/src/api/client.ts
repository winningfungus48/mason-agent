/**
 * Typed fetch helper for the Mason FastAPI backend.
 * Set `VITE_API_URL` in `.env.development` / `.env.local`.
 * Auth: Bearer token from POST /auth/login (sessionStorage), or optional `VITE_API_KEY`.
 */
import { apiBase } from '../config/apiEnv'
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
    const errObj = body as { error?: string }
    const msg = errObj?.error ?? res.statusText ?? 'Request failed'
    throw new ApiError(res.status, msg)
  }
  return body as T
}
