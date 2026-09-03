import { Activity, CheckCircle2, Database, LockKeyhole, Settings2, ShieldCheck } from 'lucide-react'

import type {
  AnalysisResult,
  RecoveryMetricsResponse,
  RecoverySimulationResponse,
} from '../features/recovery/types/recovery'
import { Button } from './ui/Button'
import { Panel } from './ui/Panel'
import { StatusBadge } from './ui/StatusBadge'

export type WorkspaceView = 'Overview' | 'Recovery Operations' | 'Simulations' | 'Learning' | 'Strategy Performance' | 'Settings'

interface SecondaryViewsProps {
  view: Exclude<WorkspaceView, 'Recovery Operations'>
  metrics: RecoveryMetricsResponse | null
  analysis: AnalysisResult | null
  simulation: RecoverySimulationResponse | null
  rewardRatio: number
  onOpenRecovery: () => void
}

function formatCurrency(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '$—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function readable(value: string | null | undefined) {
  return value ? value.replace(/_/g, ' ') : '—'
}

function MetricsSummary({ metrics }: { metrics: RecoveryMetricsResponse | null }) {
  if (!metrics) {
    return <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-3 text-sm text-[#908FA0]">Metrics will appear when the recovery API responds.</div>
  }

  return (
    <div className="grid gap-px border border-[#2D3139] bg-[#2D3139] sm:grid-cols-3">
      <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Revenue at risk</div><div className="mt-2 font-mono text-2xl text-slate-50">{formatCurrency(metrics.total_revenue_at_risk)}</div></div>
      <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Revenue recovered</div><div className="mt-2 font-mono text-2xl text-emerald-300">{formatCurrency(metrics.total_revenue_recovered)}</div></div>
      <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Recovery rate</div><div className="mt-2 font-mono text-2xl text-slate-50">{(metrics.overall_recovery_rate * 100).toFixed(1)}%</div></div>
    </div>
  )
}

export function SecondaryViews({ view, metrics, analysis, simulation, rewardRatio, onOpenRecovery }: SecondaryViewsProps) {
  if (view === 'Overview') {
    return (
      <div className="space-y-4">
        <Panel title="Overview" subtitle="A concise operating view of the recovery engine." className="p-5">
          <MetricsSummary metrics={metrics} />
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="border-l-2 border-indigo-400 bg-[#1C1F26] p-4">
              <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] text-indigo-200"><Activity className="h-4 w-4" /> Current workspace</div>
              <div className="mt-3 text-lg font-medium text-slate-50">Recovery Operations</div>
              <div className="mt-1 text-sm text-[#C7C4D7]">Select an event to analyze real failed revenue and run a safe simulation.</div>
              <Button className="mt-4" type="button" onClick={onOpenRecovery}>Open Recovery Operations</Button>
            </div>
            <div className="border border-[#2D3139] bg-[#14161A] p-4">
              <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]"><Database className="h-4 w-4 text-indigo-300" /> Data source</div>
              <div className="mt-3 text-lg font-medium text-slate-50">Live recovery metrics</div>
              <div className="mt-1 text-sm text-[#C7C4D7]">Only persisted backend responses are shown here. No synthetic history is added by the UI.</div>
            </div>
          </div>
        </Panel>
      </div>
    )
  }

  if (view === 'Simulations') {
    return (
      <Panel title="Simulations" subtitle="Current-session sandbox execution results." className="p-5">
        {simulation ? (
          <div className="grid gap-px border border-[#2D3139] bg-[#2D3139] sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Strategy</div><div className="mt-2 text-sm uppercase text-slate-50">{readable(simulation.simulation.strategy)}</div></div>
            <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Status</div><div className="mt-2 text-sm uppercase text-slate-50">{readable(simulation.simulation.status)}</div></div>
            <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Outcome</div><div className="mt-2 text-sm uppercase text-slate-50">{readable(simulation.simulation.outcome)}</div></div>
            <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Recovered</div><div className="mt-2 font-mono text-lg text-emerald-300">{formatCurrency(simulation.simulation.recovered_amount)}</div></div>
          </div>
        ) : (
          <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-3 text-sm text-[#908FA0]">No simulation result in the current session. Execute a recovery from Recovery Operations to populate this view.</div>
        )}
      </Panel>
    )
  }

  if (view === 'Learning') {
    return (
      <Panel title="Learning" subtitle="Observed outcomes and policy feedback from this session." className="p-5">
        {simulation ? (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              {['Outcome observed', 'Reward calculated', 'Policy updated', 'Next decision can adapt'].map((step, index) => (
                <div key={step} className="border-l-2 border-indigo-400 bg-[#1C1F26] p-4"><div className="font-mono text-[10px] text-[#908FA0]">0{index + 1}</div><div className="mt-2 text-sm uppercase text-slate-100">{step}</div><CheckCircle2 className="mt-4 h-4 w-4 text-emerald-300" /></div>
              ))}
            </div>
            <div className="grid gap-px border border-[#2D3139] bg-[#2D3139] sm:grid-cols-3">
              <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Observed outcome</div><div className="mt-2 uppercase text-slate-50">{readable(simulation.simulation.outcome)}</div></div>
              <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Reward</div><div className="mt-2 font-mono text-lg text-emerald-300">{(rewardRatio * 100).toFixed(1)}%</div></div>
              <div className="bg-[#14161A] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Strategy</div><div className="mt-2 uppercase text-slate-50">{readable(simulation.simulation.strategy)}</div></div>
            </div>
            <div className="border-l-2 border-amber-400 bg-amber-500/10 p-3 text-sm text-amber-100">Safety rules remain authoritative. Adaptive learning cannot override them.</div>
          </div>
        ) : (
          <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-3 text-sm text-[#908FA0]">Learning activates after a real simulation outcome is observed.</div>
        )}
      </Panel>
    )
  }

  if (view === 'Strategy Performance') {
    return (
      <Panel title="Strategy Performance" subtitle="Persisted results from GET /recovery/metrics." className="p-5">
        {!metrics || metrics.strategy_breakdown.length === 0 ? (
          <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-3 text-sm text-[#908FA0]">No recovery history yet.</div>
        ) : (
          <div className="overflow-x-auto"><table className="min-w-full text-left text-sm text-[#C7C4D7]"><thead className="bg-[#1C1F26]"><tr className="border-b border-[#2D3139] font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]"><th className="p-3">Strategy</th><th className="p-3">Cases</th><th className="p-3">Recovery Rate</th><th className="p-3">Revenue Recovered</th></tr></thead><tbody>{metrics.strategy_breakdown.map((row) => <tr key={row.strategy} className="border-b border-[#2D3139]"><td className="p-3 uppercase text-slate-100">{readable(row.strategy)}</td><td className="p-3 font-mono">{row.total_cases}</td><td className="p-3 font-mono">{(row.recovery_rate * 100).toFixed(1)}%</td><td className="p-3 font-mono text-emerald-300">{formatCurrency(row.revenue_recovered)}</td></tr>)}</tbody></table></div>
        )}
      </Panel>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Settings" subtitle="Frontend-visible environment information." className="p-5">
        <div className="space-y-3">
          <div className="flex items-center justify-between border border-[#2D3139] bg-[#14161A] p-3"><span className="flex items-center gap-2 text-sm text-[#C7C4D7]"><Settings2 className="h-4 w-4 text-indigo-300" /> API base URL</span><span className="font-mono text-xs text-[#908FA0]">Configured by VITE_API_BASE_URL</span></div>
          <div className="flex items-center justify-between border border-[#2D3139] bg-[#14161A] p-3"><span className="flex items-center gap-2 text-sm text-[#C7C4D7]"><ShieldCheck className="h-4 w-4 text-emerald-300" /> Safety authority</span><StatusBadge label="Backend enforced" tone="safe" /></div>
          <div className="flex items-center justify-between border border-[#2D3139] bg-[#14161A] p-3"><span className="flex items-center gap-2 text-sm text-[#C7C4D7]"><LockKeyhole className="h-4 w-4 text-indigo-300" /> Environment controls</span><span className="font-mono text-xs text-[#908FA0]">Informational only</span></div>
        </div>
      </Panel>
      <Panel title="Current decision" subtitle="Visible only when an analysis exists in this session." className="p-5">
        {analysis ? <div className="border-l-2 border-indigo-400 bg-[#1C1F26] p-4"><div className="font-mono text-[10px] uppercase text-[#908FA0]">Recommended strategy</div><div className="mt-2 text-lg uppercase text-slate-50">{readable(analysis.recommended_strategy)}</div><div className="mt-2 text-sm text-[#C7C4D7]">{analysis.strategy_reason}</div></div> : <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-6 text-sm text-[#908FA0]">No active decision in this session.</div>}
      </Panel>
    </div>
  )
}
