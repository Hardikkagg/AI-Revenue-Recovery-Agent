import { motion } from 'framer-motion'

import type { RecoveryMetricsResponse } from '../features/recovery/types/recovery'

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

interface KPIBarProps {
  metrics: RecoveryMetricsResponse | null
}

export function KPIBar({ metrics }: KPIBarProps) {
  const cards = [
    {
      label: 'Revenue at Risk',
      value: metrics ? formatCurrency(metrics.total_revenue_at_risk) : '$—',
      detail: metrics ? 'Across active recovery cases' : 'Awaiting recovery data',
      emphasis: false,
    },
    {
      label: 'Revenue Recovered',
      value: metrics ? formatCurrency(metrics.total_revenue_recovered) : '$—',
      detail: metrics ? 'Recovered through strategy execution' : 'Awaiting recovery data',
      emphasis: true,
    },
    {
      label: 'Recovery Rate',
      value: metrics ? percent(metrics.overall_recovery_rate) : '—',
      detail: metrics ? 'Recovery efficiency' : 'Awaiting recovery data',
      emphasis: false,
    },
    {
      label: 'Cases Resolved',
      value: metrics ? String(metrics.resolved_cases) : '—',
      detail: metrics ? `${metrics.total_cases} total tracked cases` : 'Awaiting recovery data',
      emphasis: false,
    },
    {
      label: 'Cases Escalated',
      value: metrics ? String(metrics.escalated_cases) : '—',
      detail: metrics ? 'Manual review required' : 'Awaiting recovery data',
      emphasis: false,
    },
    {
      label: 'Learning Feedback',
      value: metrics ? String(metrics.feedback_samples_count) : '—',
      detail: metrics ? 'Adaptive policy observations' : 'Awaiting recovery data',
      emphasis: false,
    },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="overflow-hidden rounded-lg border border-[#2D3139] bg-[#14161A]"
    >
      <div className="grid gap-px bg-[#2D3139] md:grid-cols-2 xl:grid-cols-3">
        {cards.map((metric) => (
          <div key={metric.label} className={`bg-[#14161A] p-4 ${metric.emphasis ? 'border-l-2 border-emerald-500 bg-[#1C1F26]' : ''}`}>
            <div className="flex items-center justify-between gap-3">
              <div className="font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-[#908FA0]">{metric.label}</div>
              {metric.emphasis && <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 font-mono text-[9px] uppercase tracking-[0.12em] text-emerald-300">Impact</span>}
            </div>
            <div className={`mt-4 font-mono font-medium tracking-tight text-slate-50 ${metric.emphasis ? 'text-4xl md:text-5xl' : 'text-3xl'}`}>
              {metric.value}
            </div>
            <div className="mt-2 text-sm text-[#908FA0]">{metric.detail}</div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
