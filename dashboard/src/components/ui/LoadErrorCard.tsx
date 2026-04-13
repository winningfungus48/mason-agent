type LoadErrorCardProps = {
  label?: string
  className?: string
}

export function LoadErrorCard({ label = 'Unable to load', className = '' }: LoadErrorCardProps) {
  return (
    <div
      className={`rounded-2xl border border-[#2a3142] bg-[#12151c]/90 px-4 py-6 text-center text-sm text-zinc-500 ${className}`}
      role="status"
    >
      {label}
    </div>
  )
}
