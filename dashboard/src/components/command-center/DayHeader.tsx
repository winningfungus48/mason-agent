type DayHeaderProps = {
  /** e.g. "Sunday, April 13, 2026" */
  dateLine: string
  summaryLine: string
}

export function DayHeader({ dateLine, summaryLine }: DayHeaderProps) {
  return (
    <header className="px-4 pb-3 pt-4 sm:px-6">
      <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-teal-400/90">
        Command center
      </p>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">{dateLine}</h1>
      <p className="mt-2 text-sm font-medium text-zinc-400">{summaryLine}</p>
    </header>
  )
}
