type SectionSkeletonProps = {
  rows?: number
  className?: string
}

export function SectionSkeleton({ rows = 3, className = '' }: SectionSkeletonProps) {
  return (
    <div className={`space-y-3 ${className}`} aria-hidden>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={`sk-${i}`}
          className="h-12 animate-pulse rounded-xl bg-[#1a1f28]"
          style={{ width: `${85 - i * 5}%` }}
        />
      ))}
    </div>
  )
}
