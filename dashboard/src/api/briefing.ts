import type { BriefingSection } from '../constants/mockData'
import type { CommandBriefExpanded } from '../constants/commandCenterMock'
import { apiJson } from './client'

export type BriefingResponse = {
  generatedAtIso: string
  sections: BriefingSection[]
}

type BriefApi = {
  error?: string
  generated_at: string | null
  weather?: string
  headlines?: string[]
  sports?: string[]
}

export async function fetchMorningBriefing(): Promise<BriefingResponse> {
  const data = await apiJson<BriefApi>('/brief')
  if (data.error || !data.generated_at) {
    return {
      generatedAtIso: '',
      sections: [{ heading: 'Brief', body: data.error ?? 'No brief available yet.' }],
    }
  }
  return {
    generatedAtIso: data.generated_at,
    sections: [
      { heading: 'Weather', body: data.weather ?? '—' },
      { heading: 'Headlines', body: (data.headlines ?? []).join('\n') },
      { heading: 'Sports', body: (data.sports ?? []).join('\n') },
    ],
  }
}

export async function fetchCommandBriefCard(): Promise<CommandBriefExpanded | null> {
  const data = await apiJson<BriefApi>('/brief')
  if (data.error || !data.generated_at) return null
  const w = data.weather ?? ''
  const tempMatch = w.match(/(\d+)\s*°?\s*F/i)
  const tempF = tempMatch ? parseInt(tempMatch[1], 10) : 72
  return {
    city: 'Houston',
    tempF,
    condition: w.slice(0, 140) || '—',
    highF: tempF,
    lowF: Math.max(0, tempF - 8),
    headlines: data.headlines?.length ? data.headlines : ['—'],
    sports: data.sports?.length ? data.sports : ['—'],
    lastUpdatedLabel: new Date(data.generated_at).toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
    }),
  }
}

export async function regenerateBriefing(): Promise<void> {
  await apiJson('/brief/regenerate', { method: 'POST', body: '{}' })
}
