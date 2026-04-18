/**
 * Google OAuth (web) — Connect Google from the dashboard; token stored on the API server.
 */
import { apiJson } from './client'
import { apiBase } from '../config/apiEnv'

export async function fetchGoogleOAuthConfig(): Promise<{ web_oauth_ready: boolean }> {
  const base = apiBase()
  if (!base) return { web_oauth_ready: false }
  try {
    const r = await fetch(`${base}/auth/google/config`)
    if (!r.ok) return { web_oauth_ready: false }
    return (await r.json()) as { web_oauth_ready: boolean }
  } catch {
    return { web_oauth_ready: false }
  }
}

/** Requires dashboard login (Bearer). Navigates browser to Google, then back to API callback. */
export async function startGoogleOAuth(): Promise<void> {
  const { authorization_url } = await apiJson<{ authorization_url: string }>('/auth/google/start', {
    method: 'POST',
  })
  window.location.href = authorization_url
}
