import { useChat } from '../../context/ChatContext'
import { ChatComposer } from '../chat/ChatComposer'
import { ChatThread } from '../chat/ChatThread'

export function DesktopChatDock() {
  const { desktopOpen, setDesktopOpen } = useChat()

  return (
    <>
      {!desktopOpen && (
        <button
          type="button"
          onClick={() => setDesktopOpen(true)}
          className="fixed bottom-6 right-6 z-40 hidden min-h-[56px] min-w-[56px] items-center justify-center rounded-full bg-teal-600 text-2xl text-white shadow-lg shadow-teal-900/40 transition hover:bg-teal-500 lg:flex"
          aria-label="Open chat"
        >
          💬
        </button>
      )}

      <div
        className={`fixed inset-0 z-[60] hidden lg:block ${
          desktopOpen ? 'pointer-events-auto' : 'pointer-events-none'
        }`}
        aria-hidden={!desktopOpen}
      >
        <button
          type="button"
          className={`absolute inset-0 bg-black/50 transition-opacity ${
            desktopOpen ? 'opacity-100' : 'opacity-0'
          }`}
          aria-label="Close chat overlay"
          onClick={() => setDesktopOpen(false)}
        />

        <div
          className={`absolute right-0 top-0 flex h-full w-full max-w-md flex-col border-l border-[#1f2430] bg-[#12151c] shadow-2xl transition-transform duration-300 ease-out ${
            desktopOpen ? 'translate-x-0' : 'pointer-events-none translate-x-full'
          }`}
          onClick={(e) => e.stopPropagation()}
          aria-hidden={!desktopOpen}
        >
          <div className="flex min-h-[52px] items-center justify-between border-b border-[#1f2430] px-4 py-3">
            <p className="text-sm font-semibold text-zinc-100">Agent chat</p>
            <button
              type="button"
              onClick={() => setDesktopOpen(false)}
              className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-zinc-500 hover:bg-[#0c0e12] hover:text-zinc-300"
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <ChatThread />
          </div>
          <ChatComposer />
        </div>
      </div>
    </>
  )
}
