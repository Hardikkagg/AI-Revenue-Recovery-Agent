type StatusType = 'safe' | 'warning' | 'danger' | 'info' | 'neutral'

interface StatusBadgeProps {
  label: string
  tone?: StatusType
}

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  const toneMap: Record<StatusType, string> = {
    safe: 'bg-emerald-500/10 text-emerald-300 ring-1 ring-inset ring-emerald-400/30',
    warning: 'bg-amber-500/10 text-amber-200 ring-1 ring-inset ring-amber-400/30',
    danger: 'bg-red-500/10 text-red-200 ring-1 ring-inset ring-red-400/30',
    info: 'bg-blue-500/10 text-blue-200 ring-1 ring-inset ring-blue-400/30',
    neutral: 'bg-slate-700/50 text-slate-200 ring-1 ring-inset ring-slate-600/60',
  }

  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] ${toneMap[tone]}`}>{label}</span>
}
