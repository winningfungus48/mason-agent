import { type FormEvent, useEffect, useRef, useState } from 'react'
import { fetchAuthMe, loginWithPassword } from '../api/auth'
import { isApiConfigured } from '../config/apiEnv'

type PasswordGateProps = {
  children: React.ReactNode
}

export function PasswordGate({ children }: PasswordGateProps) {
  const [unlocked, setUnlocked] = useState(false)
  const [checking, setChecking] = useState(true)
  const [password, setPassword] = useState('')
  const [showError, setShowError] = useState(false)
  const [errorDetail, setErrorDetail] = useState<string | null>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!isApiConfigured()) {
      setChecking(false)
      return
    }
    let cancelled = false
    fetchAuthMe()
      .then((me) => {
        if (cancelled) return
        if (me.authenticated) setUnlocked(true)
      })
      .catch(() => {
        if (cancelled) return
        setErrorDetail('Could not reach the API')
      })
      .finally(() => {
        if (!cancelled) setChecking(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (unlocked || checking) return

    function focusPassword() {
      passwordRef.current?.focus({ preventScroll: true })
    }

    focusPassword()
    const t = window.setTimeout(focusPassword, 0)

    function onVisible() {
      if (document.visibilityState === 'visible') focusPassword()
    }

    window.addEventListener('focus', focusPassword)
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      window.clearTimeout(t)
      window.removeEventListener('focus', focusPassword)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [unlocked, checking])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setShowError(false)
    setErrorDetail(null)
    if (!isApiConfigured()) return
    try {
      await loginWithPassword(password.trim())
      setUnlocked(true)
      setPassword('')
    } catch (err) {
      setShowError(true)
      setErrorDetail(err instanceof Error ? err.message : 'Login failed')
    }
  }

  if (!isApiConfigured()) {
    return (
      <div className="relative z-[100] flex min-h-screen items-center justify-center bg-[#0c0e12] p-6">
        <div className="w-full max-w-md rounded-xl border border-amber-500/30 bg-[#12151c] p-8 text-sm text-zinc-300">
          <p className="font-semibold text-amber-200/95">API URL not configured</p>
          <p className="mt-2 text-zinc-400">
            Set <code className="text-zinc-500">VITE_API_URL</code> in{' '}
            <code className="text-zinc-500">dashboard/.env.development</code> or{' '}
            <code className="text-zinc-500">.env.local</code>, then restart{' '}
            <code className="text-zinc-500">npm run dev</code>.
          </p>
        </div>
      </div>
    )
  }

  if (checking) {
    return (
      <div className="relative z-[100] flex min-h-screen items-center justify-center bg-[#0c0e12] p-6">
        <p className="text-sm text-zinc-500">Checking session…</p>
      </div>
    )
  }

  if (!unlocked) {
    return (
      <div className="relative z-[100] flex min-h-screen items-center justify-center bg-[#0c0e12] p-6">
        <div
          className="w-full max-w-sm rounded-xl border border-[#1f2430] bg-[#12151c] p-8 shadow-xl shadow-black/40"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) passwordRef.current?.focus()
          }}
        >
          <h1 className="text-center text-lg font-semibold tracking-tight text-zinc-100">
            Chief of Staff
          </h1>
          <p className="mt-1 text-center text-sm text-zinc-500">
            Sign in with your dashboard password (validated on the server)
          </p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <input
              ref={passwordRef}
              type="password"
              autoComplete="current-password"
              autoFocus
              enterKeyHint="go"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setShowError(false)
              }}
              className="w-full rounded-lg border border-[#1f2430] bg-[#0c0e12] px-3 py-2.5 text-sm text-zinc-100 outline-none ring-teal-500/30 placeholder:text-zinc-600 focus:border-teal-500/50 focus:ring-2"
              placeholder="Password"
            />
            {showError && (
              <p className="text-center text-sm text-red-400">{errorDetail ?? 'Incorrect password'}</p>
            )}
            <button
              type="submit"
              className="w-full rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-teal-500"
            >
              Unlock
            </button>
          </form>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
