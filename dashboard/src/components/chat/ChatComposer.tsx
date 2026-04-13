import { useChat } from '../../context/ChatContext'

export function ChatComposer({ className = '' }: { className?: string }) {
  const { input, setInput, handleSubmit, loading } = useChat()

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex gap-2 border-t border-[#1f2430] bg-[#0c0e12]/95 p-3 ${className}`}
    >
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Message your agent…"
        className="min-h-[44px] min-w-0 flex-1 rounded-xl border border-[#1f2430] bg-[#12151c] px-3 py-2 text-sm text-zinc-100 outline-none focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20"
      />
      <button
        type="submit"
        disabled={loading}
        className="min-h-[44px] min-w-[72px] shrink-0 rounded-xl bg-teal-600 px-4 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50"
      >
        Send
      </button>
    </form>
  )
}
