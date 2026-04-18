import { useEffect, useState } from 'react'
import { fetchGoogleOAuthConfig, startGoogleOAuth } from '../api/googleConnect'

export function ConnectGoogleBanner() {
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchGoogleOAuthConfig().then((c) => setReady(c.web_oauth_ready))
  }, [])

  if (!ready) return null

  return (
    <div className="rounded-2xl border border-teal-500/25 bg-teal-950/20 px-4 py-3 text-sm text-zinc-200">
      <p className="font-medium text-teal-200/95">Google Calendar & Tasks</p>
      <p className="mt-1 text-zinc-400">
        One-time sign-in links this dashboard (and your bot) to Google. Safe to repeat if Google revokes access.
      </p>
      <button
        type="button"
        disabled={busy}
        onClick={() => {
          setBusy(true)
          startGoogleOAuth().catch(() => setBusy(false))
        }}
        className="mt-3 rounded-lg bg-teal-600/90 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50"
      >
        {busy ? 'Redirecting…' : 'Connect Google'}
      </button>
    </div>
  )
}
