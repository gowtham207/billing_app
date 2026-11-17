export function BrandMark({ size = 36, className = '' }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={`shrink-0 ${className}`} role="img" aria-label="PeakSuite">
      <rect width="64" height="64" rx="16" fill="#102A43" />
      <path d="M30 50 41.5 24l6.2 9.2 4.8-7.4L58 50Z" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2.2" strokeLinejoin="round" />
      <path d="M46.3 25.6 50.4 33.6h-8.2Z" fill="#38BDF8" />
      <path fill="#FFFFFF" fillRule="evenodd" d="M10 15h13.8c5.7 0 9.5 3.5 9.5 8.8s-3.9 9-9.7 9H16.6V50H10V15Zm6.6 5.1v7.4h6.6c2.4 0 3.8-1.3 3.8-3.7s-1.4-3.7-3.8-3.7h-6.6Z" />
    </svg>
  )
}

export function BrandLockup({ tone = 'ink', compact = false }: { tone?: 'ink' | 'light'; compact?: boolean }) {
  const title = tone === 'light' ? 'text-white' : 'text-ink'
  const meta = tone === 'light' ? 'text-white/60' : 'text-muted'
  return (
    <div className="flex min-w-0 items-center gap-3">
      <BrandMark size={compact ? 32 : 40} />
      {compact ? null : (
        <div className="min-w-0">
          <p className={`truncate text-[15px] font-semibold tracking-tight ${title}`}>PeakSuite</p>
          <p className={`truncate text-xs ${meta}`}>Technology Peak</p>
        </div>
      )}
    </div>
  )
}
