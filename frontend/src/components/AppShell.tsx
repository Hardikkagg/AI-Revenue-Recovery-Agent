import { useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Gauge, Layers3, Sparkles, TrendingUp } from 'lucide-react'

import { useRecoveryFlow } from '../features/recovery/hooks/useRecoveryFlow'
import { KPIBar } from './KPIBar'
import { RecoveryCommandCenter } from './RecoveryCommandCenter'
import { SecondaryViews, type WorkspaceView } from './SecondaryViews'
import { Sidebar } from './Sidebar'
import { TopHeader } from './TopHeader'
import { Button } from './ui/Button'
import { Panel } from './ui/Panel'

function formatCurrency(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '$—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function AppShell() {
  const [activeView, setActiveView] = useState<WorkspaceView>('Recovery Operations')
  const {
    backendAvailable,
    metrics,
    analysis,
    simulation,
    rewardRatio,
    error,
    loading,
    refreshMetrics,
    runAnalyze,
    runSimulate,
    form,
    updateField,
    applyScenario,
    pipelineStage,
  } = useRecoveryFlow()

  const strategyBreakdown = metrics?.strategy_breakdown ?? []

  return (
    <div className="min-h-screen bg-[#0A0B0D] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-[1600px] border-x border-[#2D3139] bg-[#0A0B0D]">
        <Sidebar activeView={activeView} onNavigate={setActiveView} backendAvailable={backendAvailable} />

        <main className="flex-1 px-6 pb-8 pt-5 lg:px-8">
          <TopHeader backendAvailable={backendAvailable} hasAnalysis={Boolean(analysis)} hasSimulation={Boolean(simulation)} />

          <div className="mt-6">
            {activeView === 'Recovery Operations' ? (
              <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="space-y-4">
                  <KPIBar metrics={metrics} />
                  <RecoveryCommandCenter
                backendAvailable={backendAvailable}
                analysis={analysis}
                simulation={simulation}
                form={form}
                updateField={updateField}
                applyScenario={applyScenario}
                onAnalyze={runAnalyze}
                onSimulate={runSimulate}
                onRefresh={refreshMetrics}
                pipelineStage={pipelineStage}
                loading={loading}
                error={error}
                rewardRatio={rewardRatio}
                  />
                </div>

                <motion.aside
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="space-y-4"
            >
              <div className="panel-surface p-4">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">
                    <Sparkles className="h-3.5 w-3.5 text-blue-300" />
                    Product Signal
                  </div>
                  <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] uppercase tracking-[0.24em] text-emerald-300">
                    {backendAvailable ? 'LIVE' : 'OFFLINE'}
                  </span>
                </div>

                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                    <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400">Revenue impact</div>
                    <div className="mt-3 text-3xl font-semibold tracking-tight text-slate-50">
                      {analysis ? formatCurrency(analysis.event.amount) : '$—'}
                    </div>
                    <div className="mt-2 text-sm text-slate-400">
                      {analysis ? 'Current event value' : 'Awaiting recovery data'}
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                        <Gauge className="h-3.5 w-3.5 text-violet-300" />
                        Model readiness
                      </div>
                      <div className="mt-3 text-xl font-medium text-slate-50">{backendAvailable ? 'Production-safe' : 'API unavailable'}</div>
                    </div>
                    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                        <Layers3 className="h-3.5 w-3.5 text-emerald-300" />
                        Recovery loop
                      </div>
                      <div className="mt-3 text-xl font-medium text-slate-50">Detect → Learn</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="panel-surface p-4">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">
                  <TrendingUp className="h-3.5 w-3.5 text-emerald-300" />
                  Learning signal
                </div>
                <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Reward update</div>
                  <div className="mt-3 text-lg font-medium text-slate-50">
                    {simulation ? `${(rewardRatio * 100).toFixed(1)}% reward` : 'Awaiting learning event'}
                  </div>
                </div>
              </div>
                </motion.aside>
              </div>
            ) : (
              <SecondaryViews view={activeView} metrics={metrics} analysis={analysis} simulation={simulation} rewardRatio={rewardRatio} onOpenRecovery={() => setActiveView('Recovery Operations')} />
            )}
          </div>

          {activeView === 'Recovery Operations' && <div className="mt-6">
            <Panel title="Strategy Performance" subtitle="Live results from GET /recovery/metrics" className="p-5">
              {strategyBreakdown.length === 0 ? (
                <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-8 text-center text-sm text-[#908FA0]">
                  No recovery history yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm text-[#C7C4D7]">
                    <thead className="bg-[#1C1F26]">
                      <tr className="border-b border-[#2D3139] font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">
                        <th className="pb-3 pr-4">Strategy</th>
                        <th className="pb-3 pr-4">Cases</th>
                        <th className="pb-3 pr-4">Recovery Rate</th>
                        <th className="pb-3 pr-4">Revenue at Risk</th>
                        <th className="pb-3 pr-4">Revenue Recovered</th>
                      </tr>
                    </thead>
                    <tbody>
                      {strategyBreakdown.map((row) => (
                        <tr key={row.strategy} className="border-b border-[#2D3139] transition-colors hover:bg-[#1C1F26]">
                          <td className="py-3 pr-4 font-medium uppercase text-slate-100">{row.strategy.replace(/_/g, ' ')}</td>
                          <td className="py-3 pr-4 font-mono">{row.total_cases}</td>
                          <td className="py-3 pr-4 font-mono">{(row.recovery_rate * 100).toFixed(1)}%</td>
                          <td className="py-3 pr-4 font-mono">{formatCurrency(row.revenue_at_risk)}</td>
                          <td className="py-3 pr-4 font-mono text-emerald-300">{formatCurrency(row.revenue_recovered)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>}

          {activeView === 'Recovery Operations' && backendAvailable === false && (
            <div className="mt-6 rounded-3xl border border-red-500/30 bg-red-500/10 p-5">
              <div className="flex items-center gap-3 text-red-200">
                <AlertTriangle className="h-5 w-5" />
                <div>
                  <div className="text-[10px] uppercase tracking-[0.25em]">Backend offline</div>
                  <div className="mt-1 text-lg font-semibold">Recovery API is unavailable.</div>
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <Button type="button" variant="secondary" onClick={() => void refreshMetrics()}>Retry Connection</Button>
              </div>
            </div>
          )}

          {activeView === 'Recovery Operations' && error && backendAvailable === false && (
            <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>
          )}
        </main>
      </div>
    </div>
  )
}
