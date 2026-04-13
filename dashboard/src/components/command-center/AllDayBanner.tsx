import type { AllDayEvent } from '../../constants/commandCenterMock'

type AllDayBannerProps = {
  events: AllDayEvent[]
}

export function AllDayBanner({ events }: AllDayBannerProps) {
  if (events.length === 0) return null

  return (
    <section className="px-4 pb-3 sm:px-6" aria-label="All-day events">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
        All day
      </p>
      <div className="flex flex-wrap gap-2">
        {events.map((ev) => (
          <div
            key={ev.id}
            className="flex min-h-[40px] max-w-full items-center rounded-full border border-[#1f2430] bg-[#12151c] pl-1 pr-3 text-sm text-zinc-200"
          >
            <span
              className="mr-2 h-full min-h-[32px] w-1.5 shrink-0 rounded-full"
              style={{ backgroundColor: ev.color }}
              aria-hidden
            />
            <span className="truncate">{ev.title}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
