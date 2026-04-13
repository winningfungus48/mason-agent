import {
  createContext,
  type FormEvent,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import { sendChatMessage } from '../api/chat'
import type { ChatMessage } from '../api/chat'
import { ApiError } from '../api/client'

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

type ChatContextValue = {
  messages: ChatMessage[]
  loading: boolean
  desktopOpen: boolean
  setDesktopOpen: (open: boolean) => void
  send: (text: string) => Promise<void>
  handleSubmit: (e: FormEvent) => void
  input: string
  setInput: (v: string) => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'agent',
      text: 'Connected to your agent when VITE_API_URL and VITE_API_KEY are set in .env.local.',
      at: new Date().toISOString(),
    },
  ])
  const [loading, setLoading] = useState(false)
  const [input, setInput] = useState('')
  const [desktopOpen, setDesktopOpen] = useState(false)

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg: ChatMessage = {
      id: newId(),
      role: 'user',
      text: trimmed,
      at: new Date().toISOString(),
    }
    setMessages((m) => [...m, userMsg])
    setLoading(true)

    try {
      const prior = messages
      const reply = await sendChatMessage(trimmed, [...prior, userMsg])
      setMessages((m) => [
        ...m,
        {
          id: newId(),
          role: 'agent',
          text: reply,
          at: new Date().toISOString(),
        },
      ])
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Something went wrong'
      setMessages((m) => [
        ...m,
        {
          id: newId(),
          role: 'agent',
          text: `Error: ${msg}`,
          at: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }, [loading, messages])

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault()
      const t = input
      setInput('')
      await send(t)
    },
    [input, send],
  )

  const value = useMemo(
    () => ({
      messages,
      loading,
      desktopOpen,
      setDesktopOpen,
      send,
      handleSubmit,
      input,
      setInput,
    }),
    [messages, loading, desktopOpen, send, handleSubmit, input],
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
