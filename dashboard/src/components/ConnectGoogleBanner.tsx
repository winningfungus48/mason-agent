import { useEffect, useState } from 'react'
import { fetchGoogleOAuthConfig, startGoogleOAuth } from '../api/googleConnect'

/** One-click Google OAuth — same credentials.json as Telegram; token saved on the API server. */
export function ConnectGoogleBanner() {
  const [ready, setReady] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchGoogleOAuthConfig().then((c) => setReady(c.web_oauth_ready))
  }, [])

  if (!ready) return null

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[#2a3142] bg-[#12151c] px-3 py-2 text-sm">
      <span className="text-zinc-400">Google Calendar & Tasks</span>
      <button
        type="button"
        disabled={busy}
        onClick={() => {
          setBusy(true)
          startGoogleOAuth().catch(() => setBusy(false))
        }}
        className="rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-100 hover:bg-zinc-600 disabled:opacity-50"
      >
        {busy ? '…' : 'Connect'}
      </button>
    </div>
  )
}
