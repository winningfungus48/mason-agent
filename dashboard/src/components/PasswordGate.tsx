import { type FormEvent, useEffect, useRef, useState } from 'react'

/** Change this to rotate access; replace with real auth when the API exists. */
const DASHBOARD_PASSWORD = 'chief'

const SESSION_KEY = 'cos-dashboard-auth'

type PasswordGateProps = {
  children: React.ReactNode
}

export function PasswordGate({ children }: PasswordGateProps) {
  const [unlocked, setUnlocked] = useState(false)
  const [password, setPassword] = useState('')
  const [showError, setShowError] = useState(false)
  const passwordRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (sessionStorage.getItem(SESSION_KEY) === '1') {
      setUnlocked(true)
    }
  }, [])

  /** Popped-out / embedded previews often lose input focus; restore when the gate is shown. */
  useEffect(() => {
    if (unlocked) return

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
  }, [unlocked])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (password === DASHBOARD_PASSWORD) {
      sessionStorage.setItem(SESSION_KEY, '1')
      setShowError(false)
      setUnlocked(true)
    } else {
      setShowError(true)
    }
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
          <p className="mt-1 text-center text-sm text-zinc-500">Enter dashboard password</p>
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
              <p className="text-center text-sm text-red-400">Incorrect password</p>
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
