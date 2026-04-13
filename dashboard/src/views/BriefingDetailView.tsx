import { useEffect, useState } from 'react'
import { fetchMorningBriefing, regenerateBriefing } from '../api/briefing'
import { LoadErrorCard } from '../components/ui/LoadErrorCard'
import { SectionSkeleton } from '../components/ui/SectionSkeleton'
import type { BriefingSection } from '../constants/mockData'

function formatGenerated(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

export function BriefingDetailView() {
  const [generatedAt, setGeneratedAt] = useState('')
  const [sections, setSections] = useState<BriefingSection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [regenBusy, setRegenBusy] = useState(false)

  function load() {
    return fetchMorningBriefing()
      .then((res) => {
        setGeneratedAt(res.generatedAtIso)
        setSections(res.sections)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function onRegenerate() {
    setRegenBusy(true)
    try {
      await regenerateBriefing()
      window.alert('Brief regeneration started — check back in a minute.')
    } catch (e) {
      window.alert(e instanceof Error ? e.message : 'Failed to start regeneration')
    } finally {
      setRegenBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <SectionSkeleton rows={6} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
        <LoadErrorCard label="Unable to load briefing" />
      </div>
    )
  }

  return (
    <div className="px-4 pb-8 pt-4 sm:px-6 lg:px-8 lg:pt-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500">
        <span>Last generated: {generatedAt ? formatGenerated(generatedAt) : '—'}</span>
        <button
          type="button"
          disabled={regenBusy}
          onClick={onRegenerate}
          className="min-h-[44px] rounded-xl border border-[#2a3142] bg-[#12151c] px-4 text-xs font-medium text-zinc-300 hover:border-teal-500/40 disabled:opacity-50"
        >
          {regenBusy ? 'Starting…' : 'Regenerate'}
        </button>
      </div>
      <div className="space-y-6">
        {sections.map((s) => (
          <article key={s.heading} className="rounded-2xl border border-[#1f2430] bg-[#12151c] p-5">
            <h2 className="text-sm font-semibold text-teal-400/90">{s.heading}</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-zinc-400">{s.body}</p>
          </article>
        ))}
      </div>
    </div>
  )
}
