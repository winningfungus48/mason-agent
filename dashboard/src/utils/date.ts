/** Local YYYY-MM-DD for the user's calendar date. */
export function todayIsoDate() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Local calendar date tomorrow as YYYY-MM-DD. */
export function tomorrowIsoDate() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Monday-based week: 0 = Mon … 6 = Sun for a given date. */
export function mondayIndex(d: Date) {
  const day = d.getDay()
  return day === 0 ? 6 : day - 1
}
