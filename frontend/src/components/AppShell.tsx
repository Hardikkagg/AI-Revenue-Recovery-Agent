import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'

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
    <div className="min-h-screen bg-[#F4F6F8] text-[#1F2937]">
      <div className="mx-auto flex min-h-screen max-w-[1600px] border-x border-[#D9E0E7] bg-[#F4F6F8]">
        <Sidebar activeView={activeView} onNavigate={setActiveView} backendAvailable={backendAvailable} />

        <main className="flex-1 px-5 pb-8 pt-5 lg:px-8">
          <TopHeader backendAvailable={backendAvailable} hasAnalysis={Boolean(analysis)} hasSimulation={Boolean(simulation)} />

          <div className="mt-6">
            {activeView === 'Recovery Operations' ? (
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

        </main>
      </div>
    </div>
  )
}
