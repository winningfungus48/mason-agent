import { type ReactNode, useEffect } from 'react'

type BottomSheetProps = {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

/** Mobile: bottom sheet. Desktop (lg+): centered dialog. */
export function BottomSheet({ open, onClose, title, children }: BottomSheetProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[90] flex items-end justify-center lg:items-center lg:p-6">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-[2px]"
        aria-label="Close"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="bottom-sheet-title"
        className="relative z-10 flex max-h-[min(85vh,800px)] w-full max-w-lg flex-col rounded-t-2xl border border-[#1f2430] bg-[#12151c] shadow-2xl motion-safe:transition-transform motion-safe:duration-200 lg:max-h-[min(90vh,720px)] lg:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 flex-col items-center border-b border-[#1f2430] px-4 pb-3 pt-3 sm:px-5">
          <div className="mb-2 h-1 w-10 rounded-full bg-zinc-600 lg:hidden" aria-hidden />
          <h2
            id="bottom-sheet-title"
            className="w-full text-center text-base font-semibold text-zinc-100 lg:text-left lg:text-lg"
          >
            {title}
          </h2>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">{children}</div>
        <div className="shrink-0 border-t border-[#1f2430] p-3">
          <button
            type="button"
            onClick={onClose}
            className="min-h-[44px] w-full rounded-xl border border-[#2a3142] bg-[#0c0e12] text-sm font-medium text-zinc-300 hover:bg-[#1a1f2e]"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
