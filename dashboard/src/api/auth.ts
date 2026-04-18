import { apiBase, ngrokSkipHeaders } from '../config/apiEnv'

const TOKEN_KEY = 'mason_access_token'

export function getAccessToken(): string {
  return sessionStorage.getItem(TOKEN_KEY) ?? ''
}

export function setAccessToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken() {
  sessionStorage.removeItem(TOKEN_KEY)
}

export async function loginWithPassword(password: string): Promise<void> {
  const base = apiBase()
  if (!base) throw new Error('VITE_API_URL is not set')
  const res = await fetch(`${base}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...ngrokSkipHeaders() },
    body: JSON.stringify({ password }),
  })
  const text = await res.text()
  let body: { access_token?: string; error?: string } = {}
  try {
    body = text ? JSON.parse(text) : {}
  } catch {
    body = { error: text || 'Bad response' }
  }
  if (!res.ok) {
    throw new Error(body.error ?? res.statusText)
  }
  if (!body.access_token) {
    throw new Error('No access token returned')
  }
  setAccessToken(body.access_token)
}

export async function fetchAuthMe(): Promise<{ authenticated: boolean; via?: string }> {
  const base = apiBase()
  if (!base) return { authenticated: false }
  const token = getAccessToken()
  const headers = new Headers({ ...ngrokSkipHeaders() })
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${base}/auth/me`, { headers })
  const data = (await res.json()) as { authenticated: boolean; via?: string }
  return data
}

export async function logoutRemote() {
  const base = apiBase()
  if (!base) return
  const token = getAccessToken()
  try {
    await fetch(`${base}/auth/logout`, {
      method: 'POST',
      headers: {
        ...ngrokSkipHeaders(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
  } catch {
    /* ignore */
  }
  clearAccessToken()
}
