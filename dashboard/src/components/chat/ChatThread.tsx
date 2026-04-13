import { useChat } from '../../context/ChatContext'

export function ChatThread({ className = '' }: { className?: string }) {
  const { messages, loading } = useChat()

  return (
    <div className={`space-y-3 ${className}`}>
      {messages.map((m) => (
        <div
          key={m.id}
          className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] rounded-2xl px-3 py-2.5 text-sm leading-snug ${
              m.role === 'user'
                ? 'bg-teal-600/90 text-white'
                : 'border border-[#1f2430] bg-[#0c0e12] text-zinc-300'
            }`}
          >
            {m.text}
          </div>
        </div>
      ))}
      {loading && (
        <div className="flex justify-start">
          <div className="rounded-2xl border border-[#1f2430] bg-[#0c0e12] px-3 py-2.5 text-xs text-zinc-500">
            <span className="animate-pulse">●●●</span> Agent typing…
          </div>
        </div>
      )}
    </div>
  )
}
