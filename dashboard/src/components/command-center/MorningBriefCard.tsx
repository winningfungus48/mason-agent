import { useState } from 'react'
import type { CommandBriefExpanded } from '../../constants/commandCenterMock'

type MorningBriefCardProps = {
  brief: CommandBriefExpanded
  deEmphasize: boolean
  /** Desktop column: always expanded, no collapse control. */
  variant: 'mobile' | 'desktop'
}

export function MorningBriefCard({ brief, deEmphasize, variant }: MorningBriefCardProps) {
  const [expanded, setExpanded] = useState(false)
  const isOpen = variant === 'desktop' ? true : expanded

  const tone = deEmphasize ? 'opacity-60 sm:scale-[0.99]' : 'opacity-100'

  const headerInner = (
    <>
      <span className="text-2xl" aria-hidden>
        🌤
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Morning brief</p>
        <p className={`mt-1 font-semibold text-zinc-100 ${deEmphasize ? 'text-base' : 'text-lg'}`}>
          {brief.tempF}°
        </p>
        <p className={`text-zinc-400 ${deEmphasize ? 'text-xs' : 'text-sm'}`}>{brief.condition}</p>
        <p className="mt-2 line-clamp-2 text-sm text-zinc-300">{brief.headlines[0]}</p>
        {variant === 'mobile' && (
          <p className="mt-2 text-xs text-teal-500/90">
            {isOpen ? 'Tap to collapse' : 'Tap to expand'}{' '}
            <span className="inline-block transition-transform">{isOpen ? '▾' : '▸'}</span>
          </p>
        )}
      </div>
    </>
  )

  return (
    <section
      className={`rounded-2xl border border-[#1f2430] bg-[#12151c] transition-[opacity,transform] duration-300 ${tone}`}
    >
      {variant === 'mobile' ? (
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="flex w-full min-h-[44px] items-start gap-3 p-4 text-left"
          aria-expanded={isOpen}
        >
          {headerInner}
        </button>
      ) : (
        <div className="flex items-start gap-3 p-4">{headerInner}</div>
      )}

      {isOpen && (
        <div className="motion-safe:animate-[cos-brief-expand_0.25s_ease-out] space-y-4 border-t border-[#1f2430] px-4 pb-4 pt-3">
          <section>
            <h3 className="text-xs font-semibold text-teal-400/90">🌤 Weather</h3>
            <p className="mt-1 text-sm text-zinc-300">
              {brief.city} · {brief.condition} · High {brief.highF}° / Low {brief.lowF}°
            </p>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-teal-400/90">📰 Top Headlines</h3>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-zinc-400">
              {brief.headlines.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </section>
          <section>
            <h3 className="text-xs font-semibold text-teal-400/90">🏈 Sports</h3>
            <ul className="mt-2 space-y-1 text-sm text-zinc-400">
              {brief.sports.map((s) => (
                <li key={s}>• {s}</li>
              ))}
            </ul>
          </section>
          <p className="text-xs text-zinc-500">
            Last updated: {brief.lastUpdatedLabel} ·{' '}
            <button type="button" className="text-teal-400 hover:underline">
              Regenerate
            </button>
          </p>
        </div>
      )}
    </section>
  )
}
