import { ChatComposer } from '../components/chat/ChatComposer'
import { ChatThread } from '../components/chat/ChatThread'

/** Full-screen chat on small screens (Chat tab). Hidden on lg+ where the dock is used. */
export function MobileChatView() {
  return (
    <div className="flex min-h-0 flex-1 flex-col lg:hidden">
      <div className="border-b border-[#1f2430] px-4 py-3">
        <p className="text-sm font-semibold text-zinc-100">Agent chat</p>
        <p className="text-xs text-zinc-500">Uses POST /chat when the API is configured</p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden p-4">
        <ChatThread />
      </div>
      <div className="shrink-0">
        <ChatComposer />
      </div>
    </div>
  )
}
