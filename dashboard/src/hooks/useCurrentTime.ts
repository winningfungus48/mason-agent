import { useEffect, useState } from 'react'

/** Re-renders every 60s for time-aware UI. */
export function useCurrentTime() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000)
    return () => window.clearInterval(id)
  }, [])

  return now
}
