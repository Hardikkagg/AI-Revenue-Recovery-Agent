type StatusType = 'safe' | 'warning' | 'danger' | 'info' | 'neutral'

interface StatusBadgeProps {
  label: string
  tone?: StatusType
}

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  const toneMap: Record<StatusType, string> = {
    safe: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
    warning: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
    danger: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
    info: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200',
    neutral: 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200',
  }

  return <span className={`inline-flex items-center rounded px-2 py-1 text-[11px] font-semibold ${toneMap[tone]}`}>{label}</span>
}
