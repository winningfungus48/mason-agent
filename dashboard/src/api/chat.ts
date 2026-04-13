import { apiJson } from './client'

export type ChatMessage = {
  id: string
  role: 'user' | 'agent'
  text: string
  at: string
}

type ChatApiBody = {
  role: string
  content: string
}

export async function sendChatMessage(text: string, priorMessages: ChatMessage[]): Promise<string> {
  const history: ChatApiBody[] = priorMessages.map((m) => ({
    role: m.role === 'user' ? 'user' : 'assistant',
    content: m.text,
  }))
  const data = await apiJson<{ response: string; timestamp: string }>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message: text, history }),
  })
  return data.response ?? ''
}
