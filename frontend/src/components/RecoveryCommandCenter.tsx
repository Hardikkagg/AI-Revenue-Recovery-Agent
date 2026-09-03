import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Bot,
  BrainCircuit,
  Check,
  CircleDashed,
  CreditCard,
  Gauge,
  LoaderCircle,
  ShieldAlert,
  ShoppingCart,
  Sparkles,
  Workflow,
} from 'lucide-react'

import type {
  AnalysisResult,
  RecoveryEventInput,
  RecoverySimulationResponse,
} from '../features/recovery/types/recovery'
import { scenarioPresets } from '../features/recovery/hooks/useRecoveryFlow'
import { Button } from './ui/Button'
import { Panel } from './ui/Panel'
import { StatusBadge } from './ui/StatusBadge'

const pipelineStages = ['DETECT', 'DIAGNOSE', 'SCORE', 'STRATEGY', 'EXECUTE', 'OBSERVE', 'LEARN'] as const

type PipelineStage = (typeof pipelineStages)[number] | 'OUTCOME'

interface RecoveryCommandCenterProps {
  backendAvailable: boolean | null
  analysis: AnalysisResult | null
  simulation: RecoverySimulationResponse | null
  form: RecoveryEventInput
  updateField: (key: keyof RecoveryEventInput, value: string | number | null) => void
  applyScenario: (scenario: 'paymentFailure' | 'checkoutAbandonment' | 'fraudHold') => void
  onAnalyze: () => Promise<AnalysisResult | null | undefined>
  onSimulate: () => Promise<RecoverySimulationResponse | null | undefined>
  onRefresh: () => Promise<unknown>
  pipelineStage: PipelineStage | null
  loading: 'idle' | 'analyzing' | 'simulating'
  error: string | null
  rewardRatio: number
}

function formatCurrency(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '$—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

function readableStrategy(value: string | null | undefined) {
  return value ? value.replace(/_/g, ' ') : '—'
}

export function RecoveryCommandCenter({
  backendAvailable,
  analysis,
  simulation,
  form,
  updateField,
  applyScenario,
  onAnalyze,
  onSimulate,
  onRefresh,
  pipelineStage,
  loading,
  error,
  rewardRatio,
}: RecoveryCommandCenterProps) {
  const activeStage = pipelineStage === 'OUTCOME' ? 'OBSERVE' : pipelineStage ?? 'DETECT'
  const activeIndex = pipelineStages.indexOf(activeStage)
  const probability = analysis ? Math.round(analysis.recovery_probability * 100) : 0
  const isBlocked = analysis?.recommended_strategy === 'escalate_to_manual_review'
  const safeTone = analysis?.recommended_strategy === 'escalate_to_manual_review' ? 'danger' : 'safe'
  const safeLabel = analysis?.recommended_strategy === 'escalate_to_manual_review' ? 'MANUAL REVIEW' : 'SAFE TO AUTOMATE'

  const pipeline = pipelineStages.map((stage, index) => {
    const isCurrent = activeIndex === index
    const isComplete = activeIndex > index || (index === pipelineStages.length - 1 && Boolean(simulation))
    const isBlockedStage = isBlocked && stage === 'STRATEGY'

    return {
      name: stage,
      description: {
        DETECT: 'Event identified',
        DIAGNOSE: 'Failure cause understood',
        SCORE: 'Recovery likelihood estimated',
        STRATEGY: isBlockedStage ? 'Safety policy blocked automation' : 'Safest action selected',
        EXECUTE: 'Sandbox execution',
        OBSERVE: 'Outcome measured',
        LEARN: 'Policy feedback recorded',
      }[stage],
      status: isBlockedStage ? 'blocked' : isComplete ? 'complete' : isCurrent ? 'active' : 'pending',
    }
  })

  return (
    <div className="space-y-4">
      <Panel title="Decision Pipeline" subtitle="Detect → diagnose → score → strategy → execute → observe → learn" className="p-5">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#908FA0]">
            <Workflow className="h-4 w-4 text-indigo-300" />
            Live case lifecycle
          </div>
          <StatusBadge label={safeLabel} tone={analysis ? (safeTone as 'safe' | 'danger') : 'neutral'} />
        </div>

        <div className="relative grid gap-2 md:grid-cols-7">
          <div className="absolute left-[7%] right-[7%] top-5 hidden h-px bg-[#2D3139] md:block" />
          {pipeline.map((step, index) => (
            <motion.div
              key={step.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.25 }}
              className={`relative z-10 min-w-0 border-l-2 bg-[#14161A] px-2.5 py-2.5 transition-colors duration-300 ${
                step.status === 'complete'
                  ? 'border-emerald-500/70'
                  : step.status === 'active'
                    ? 'border-indigo-400 bg-[#1C1F26]'
                    : step.status === 'blocked'
                      ? 'border-red-500/70 bg-red-500/5'
                      : 'border-[#2D3139]'
              }`}
            >
              <div className="mb-2 flex items-center justify-between font-mono text-[10px] text-[#908FA0]">
                <span>0{index + 1}</span>
                {step.status === 'complete' ? <Check className="h-3.5 w-3.5 text-emerald-300" /> : step.status === 'active' ? <LoaderCircle className="h-3.5 w-3.5 text-indigo-300" /> : step.status === 'blocked' ? <ShieldAlert className="h-3.5 w-3.5 text-red-300" /> : <CircleDashed className="h-3.5 w-3.5 text-[#908FA0]" />}
              </div>
              <div className={`font-mono text-[10px] font-medium uppercase tracking-[0.12em] ${step.status === 'complete' ? 'text-emerald-300' : step.status === 'active' ? 'text-indigo-200' : step.status === 'blocked' ? 'text-red-300' : 'text-[#908FA0]'}`}>{step.name}</div>
              <div className="mt-2 min-h-9 text-xs leading-4 text-[#C7C4D7]">{step.description}</div>
              <div className={`mt-2 font-mono text-[9px] uppercase tracking-[0.12em] ${step.status === 'complete' ? 'text-emerald-400/70' : step.status === 'active' ? 'text-indigo-300' : step.status === 'blocked' ? 'text-red-300' : 'text-[#908FA0]'}`}>
                {step.status === 'complete' ? 'Completed' : step.status === 'active' ? 'Active' : step.status === 'blocked' ? 'Blocked' : 'Pending'}
              </div>
            </motion.div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Recovery Event" subtitle="Feed a failed-revenue event into the recovery engine." className="p-5">
          <div className="space-y-5">
            <div className="space-y-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#908FA0]">Scenario presets</div>
              <div className="grid gap-3 md:grid-cols-3">
                {[
                  { key: 'paymentFailure', label: 'Payment Failure', icon: CreditCard, description: 'Network error', preset: scenarioPresets.paymentFailure },
                  { key: 'checkoutAbandonment', label: 'Checkout Abandonment', icon: ShoppingCart, description: 'Cart hesitation', preset: scenarioPresets.checkoutAbandonment },
                  { key: 'fraudHold', label: 'Fraud Hold', icon: ShieldAlert, description: 'Safety escalation', preset: scenarioPresets.fraudHold },
                ].map((scenario) => (
                  <button
                    key={scenario.key}
                    type="button"
                    className={`group rounded border p-3 text-left transition-colors duration-200 ${form.event_type === scenario.preset.event_type && form.failure_reason === scenario.preset.failure_reason ? 'border-indigo-400 bg-indigo-500/10' : 'border-[#2D3139] bg-[#0A0B0D] hover:border-indigo-400/50 hover:bg-[#1C1F26]'}`}
                    onClick={() => applyScenario(scenario.key as 'paymentFailure' | 'checkoutAbandonment' | 'fraudHold')}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <scenario.icon className="h-4 w-4 text-indigo-300" />
                      <span className="font-mono text-[9px] text-[#908FA0]">{scenario.key === 'paymentFailure' ? '01' : scenario.key === 'checkoutAbandonment' ? '02' : '03'}</span>
                    </div>
                    <div className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-200">{scenario.label}</div>
                    <div className="mt-2 text-xs text-[#908FA0]">{scenario.description}</div>
                    <div className="mt-3 flex items-center justify-between gap-2 font-mono text-[10px] uppercase tracking-[0.1em] text-[#C7C4D7]"><span>{scenario.preset.failure_reason}</span><span>{formatCurrency(scenario.preset.amount)}</span></div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Customer ID</span>
                <input
                  value={Number(form.customer_id ?? 0)}
                  onChange={(event) => updateField('customer_id', Number(event.target.value))}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Event Type</span>
                <select
                  value={String(form.event_type ?? 'payment_failure')}
                  onChange={(event) => updateField('event_type', event.target.value)}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                >
                  <option value="payment_failure">Payment Failure</option>
                  <option value="checkout_abandonment">Checkout Abandonment</option>
                  <option value="subscription_failure">Subscription Failure</option>
                </select>
              </label>
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Amount</span>
                <input
                  type="number"
                  value={Number(form.amount ?? 0)}
                  onChange={(event) => updateField('amount', Number(event.target.value))}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Payment Method</span>
                <input
                  value={String(form.payment_method ?? '')}
                  onChange={(event) => updateField('payment_method', event.target.value)}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
              <label className="space-y-2 md:col-span-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Failure Reason</span>
                <input
                  value={String(form.failure_reason ?? '')}
                  onChange={(event) => updateField('failure_reason', event.target.value)}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Retry Count</span>
                <input
                  type="number"
                  value={Number(form.retry_count ?? 0)}
                  onChange={(event) => updateField('retry_count', Number(event.target.value))}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
              <label className="space-y-2">
                <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Checkout Visits</span>
                <input
                  type="number"
                  value={Number(form.checkout_visits ?? 0)}
                  onChange={(event) => updateField('checkout_visits', Number(event.target.value))}
                  className="w-full rounded border border-[#2D3139] bg-[#0A0B0D] px-3 py-2.5 text-sm text-slate-50 outline-none transition focus:border-indigo-400"
                />
              </label>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <Button type="button" onClick={() => void onAnalyze()} disabled={backendAvailable !== true || loading !== 'idle'}>
                {loading === 'analyzing' ? 'Analyzing…' : 'Analyze Recovery'}
              </Button>
              <Button type="button" variant="secondary" onClick={() => void onRefresh()} disabled={backendAvailable !== true}>
                Refresh Metrics
              </Button>
            </div>

            {error && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>
            )}
          </div>
        </Panel>

        <Panel title="AI Decision" subtitle={analysis ? 'Decision generated by the live backend' : 'Awaiting live analysis'} className="p-5">
          <div className="space-y-4">
            <div className="border-l-2 border-indigo-400 bg-[#1C1F26] p-4">
              <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-indigo-300">
                <Gauge className="h-4 w-4" />
                Recovery probability
              </div>
              <div className="mt-3 flex items-end justify-between gap-4">
                <div className="font-mono text-5xl font-medium tracking-tight text-slate-50">{analysis ? `${probability}%` : '—'}</div>
                <div className="pb-1 text-right text-xs text-[#908FA0]">{analysis ? 'Backend score' : 'Awaiting analysis'}</div>
              </div>
              <div className="mt-4 h-2 overflow-hidden bg-[#0A0B0D]">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: analysis ? `${Math.min(probability, 100)}%` : '0%' }}
                  transition={{ duration: 0.55, ease: 'easeOut' }}
                  className="h-full bg-indigo-400"
                />
              </div>
            </div>

            <div className="border border-[#2D3139] bg-[#14161A] p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#908FA0]">
                  <Bot className="h-4 w-4 text-indigo-300" />
                  Recommended strategy
                </div>
                <StatusBadge label={analysis ? analysis.recommended_strategy : 'Awaiting analysis'} tone={analysis ? (analysis.recommended_strategy === 'escalate_to_manual_review' ? 'danger' : 'info') : 'neutral'} />
              </div>
              <div className="mt-3 text-2xl font-semibold uppercase tracking-tight text-slate-50">
                {analysis ? analysis.recommended_strategy.replace(/_/g, ' ') : '—'}
              </div>
              <div className="mt-2 text-sm leading-6 text-[#C7C4D7]">
                {analysis ? analysis.strategy_reason : 'Run an analysis to generate a backend decision.'}
              </div>
            </div>

            <div className="grid gap-px border border-[#2D3139] bg-[#2D3139] text-sm text-slate-300 sm:grid-cols-3">
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Diagnosis</div>
                <div className="mt-2 font-medium text-slate-100">{analysis ? analysis.diagnosis.diagnosis_text : '—'}</div>
              </div>
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Recoverability</div>
                <div className="mt-2 font-medium text-slate-100">{analysis ? analysis.diagnosis.recoverability : '—'}</div>
              </div>
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Confidence</div>
                <div className="mt-2 font-medium text-slate-100">{analysis ? analysis.confidence : '—'}</div>
              </div>
            </div>

            <div className="border-l-2 border-[#2D3139] bg-[#14161A] px-4 py-3 text-sm leading-6 text-[#C7C4D7]">
              <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Score factors</div>
              {analysis ? analysis.score_factors.join(', ') : '—'}
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel title="AI Reasoning" subtitle="Why the recovery engine selected this strategy." className="p-5">
          <div className="space-y-4">
            {analysis?.llm_generation ? (
              <>
                <div className="border-l-2 border-indigo-400 bg-[#1C1F26] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-indigo-200">
                    <BrainCircuit className="h-3.5 w-3.5 text-blue-300" />
                      Reasoning source
                    </div>
                    <StatusBadge label={analysis.llm_generation.fallback_used ? 'Deterministic fallback' : 'LLM generated'} tone={analysis.llm_generation.fallback_used ? 'warning' : 'info'} />
                  </div>
                  <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.1em] text-[#908FA0]">{analysis.llm_generation.provider} / {analysis.llm_generation.model}</div>
                  <p className="mt-4 text-sm leading-6 text-[#C7C4D7]">{analysis.llm_generation.reasoning}</p>
                  {analysis.llm_generation.fallback_used && analysis.llm_generation.fallback_reason && (
                    <div className="mt-3 border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                      {analysis.llm_generation.fallback_reason}
                    </div>
                  )}
                </div>
                <div className="border border-[#2D3139] bg-[#14161A] p-4">
                  <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#908FA0]">
                    <Sparkles className="h-3.5 w-3.5 text-violet-300" />
                    Customer-facing message
                  </div>
                  <div className="mt-3 whitespace-pre-line border-l border-[#2D3139] pl-3 text-sm leading-6 text-[#C7C4D7]">
                    {analysis.llm_generation.customer_message ?? 'No customer message generated for this strategy.'}
                  </div>
                </div>
              </>
            ) : (
              <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-5 text-sm text-[#908FA0]">
                Reasoning will appear after the recovery engine analyzes an event.
              </div>
            )}
          </div>
        </Panel>

        <Panel title="Execution" subtitle={simulation ? 'Observed result from the recovery sandbox.' : 'Ready to execute the selected strategy.'} className="p-5">
          <div className="space-y-4">
            <div className={`border-l-2 p-4 ${simulation?.simulation.status === 'completed' ? 'border-emerald-500 bg-emerald-500/5' : simulation?.simulation.status === 'escalated' || isBlocked ? 'border-red-500 bg-red-500/5' : 'border-indigo-400 bg-[#1C1F26]'}`}>
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#908FA0]">{simulation ? 'Recovery executed' : isBlocked ? 'Automation blocked' : 'Ready to execute'}</div>
                <div className={`mt-2 font-mono text-2xl font-medium uppercase tracking-tight ${simulation?.simulation.status === 'completed' ? 'text-emerald-300' : simulation?.simulation.status === 'escalated' || isBlocked ? 'text-red-300' : 'text-slate-50'}`}>
                  {simulation ? formatCurrency(simulation.simulation.recovered_amount) : readableStrategy(analysis?.recommended_strategy)}
                </div>
                <div className="mt-1 text-sm text-[#C7C4D7]">{simulation ? readableStrategy(simulation.simulation.outcome) : `Amount at risk: ${formatCurrency(analysis?.event.amount ?? form.amount)}`}</div>
              </div>
              <div className="mt-3"><StatusBadge label={simulation ? readableStrategy(simulation.simulation.status) : isBlocked ? 'Blocked' : 'Ready'} tone={simulation ? (simulation.simulation.status === 'escalated' ? 'danger' : 'safe') : isBlocked ? 'danger' : 'info'} /></div>
            </div>

            <div className="grid gap-px border border-[#2D3139] bg-[#2D3139] sm:grid-cols-2">
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Amount at risk</div>
                <div className="mt-2 font-mono text-lg text-slate-100">{simulation ? formatCurrency(simulation.simulation.amount_at_risk) : formatCurrency(analysis?.event.amount ?? form.amount)}</div>
              </div>
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Strategy used</div>
                <div className="mt-2 text-sm font-medium uppercase text-slate-100">{simulation ? readableStrategy(simulation.simulation.strategy) : readableStrategy(analysis?.recommended_strategy)}</div>
              </div>
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Recovered</div>
                <div className={`mt-2 font-mono text-xl ${simulation?.simulation.status === 'completed' ? 'text-emerald-300' : 'text-slate-100'}`}>{simulation ? formatCurrency(simulation.simulation.recovered_amount) : '$—'}</div>
              </div>
              <div className="bg-[#14161A] p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Execution time</div>
                <div className="mt-2 font-mono text-lg text-slate-100">{simulation ? `${simulation.simulation.execution_time_seconds.toFixed(3)} sec` : '—'}</div>
              </div>
            </div>

            <div className="pt-1">
              <Button
                type="button"
                className="w-full"
                onClick={() => void onSimulate()}
                disabled={!analysis || backendAvailable !== true || loading !== 'idle' || isBlocked}
              >
                {loading === 'simulating' ? 'Executing...' : isBlocked ? 'Automation blocked' : 'Execute Recovery'}
              </Button>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Learning" subtitle="Outcome → reward → policy update → next decision." className="p-5">
          {simulation ? (
            <div className="border border-[#2D3139] bg-[#14161A] p-4">
              <div className="grid gap-2 font-mono text-[10px] uppercase tracking-[0.1em] text-[#C7C4D7] sm:grid-cols-4">
                <span className="border-l-2 border-emerald-500 pl-2">Outcome observed</span>
                <span className="text-slate-500">↓</span>
                <span className="border-l-2 border-indigo-400 pl-2">Reward calculated</span>
                <span className="border-l-2 border-indigo-400 pl-2">Policy updated</span>
              </div>
              <div className="mt-5 grid gap-px border border-[#2D3139] bg-[#2D3139] sm:grid-cols-2">
                <div className="bg-[#14161A] p-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Observed outcome</div>
                  <div className="mt-2 text-sm font-medium uppercase text-slate-100">{readableStrategy(simulation.simulation.outcome)}</div>
                </div>
                <div className="bg-[#14161A] p-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Reward</div>
                  <div className="mt-2 font-mono text-lg text-emerald-300">{(rewardRatio * 100).toFixed(1)}%</div>
                </div>
                <div className="bg-[#14161A] p-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Recovered amount</div>
                  <div className="mt-2 font-mono text-lg text-slate-50">{formatCurrency(simulation.simulation.recovered_amount)}</div>
                </div>
                <div className="bg-[#14161A] p-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Strategy</div>
                  <div className="mt-2 text-sm font-medium uppercase text-slate-50">{readableStrategy(simulation.simulation.strategy)}</div>
                </div>
              </div>
              <div className="mt-4 border-l-2 border-indigo-400 pl-3 text-sm leading-6 text-[#C7C4D7]">
                Observed outcome added to the adaptive policy. Future comparable decisions may adapt.
              </div>
            </div>
          ) : (
            <div className="border border-dashed border-[#2D3139] bg-[#14161A] p-6 text-sm text-[#908FA0]">
              No learning event yet. Execute a recovery strategy to update the adaptive learning loop.
            </div>
          )}
        </Panel>

        <Panel title="Safety & Guardrails" subtitle="AI proposes. Deterministic safety rules authorize." className="p-5">
          {analysis?.recommended_strategy === 'escalate_to_manual_review' || simulation?.simulation.status === 'escalated' ? (
            <div className="border-l-2 border-red-500 bg-red-500/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.24em] text-red-200">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Manual review required
                </div>
                <StatusBadge label="ESCALATED" tone="danger" />
              </div>
              <div className="mt-3 space-y-2 text-sm leading-6 text-slate-200">
                <div>Deterministic safety rules prevented automated execution.</div>
                {analysis && <div className="font-mono text-xs text-red-200">Diagnosis: {analysis.diagnosis.diagnosis_code} / Recoverability: {analysis.diagnosis.recoverability}</div>}
                {simulation && <div className="font-mono text-xs text-red-200">Outcome: {readableStrategy(simulation.simulation.outcome)} / Recovered: {formatCurrency(simulation.simulation.recovered_amount)}</div>}
                <div className="text-[#C7C4D7]">Adaptive learning cannot override safety policy.</div>
              </div>
            </div>
          ) : (
            <div className="border-l-2 border-emerald-500 bg-emerald-500/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.24em] text-emerald-200">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Safe to automate
                </div>
                <StatusBadge label="SAFE" tone="safe" />
              </div>
              <div className="mt-3 text-sm leading-6 text-slate-200">
                Deterministic safety gates passed. Adaptive learning may recommend among approved strategies, but it does not override safety policy.
              </div>
            </div>
          )}

          {simulation?.simulation.gateway_result && (
            <div className="mt-4 border border-[#2D3139] bg-[#14161A] p-4 text-sm text-[#C7C4D7]">
              <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Gateway result</div>
              <div className="mt-2">{simulation.simulation.gateway_result.response_message}</div>
            </div>
          )}

          {simulation?.simulation.communication_result && (
            <div className="mt-4 border border-[#2D3139] bg-[#14161A] p-4 text-sm text-[#C7C4D7]">
              <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-[#908FA0]">Customer outreach</div>
              <div className="mt-2 whitespace-pre-line">{simulation.simulation.communication_result.message}</div>
            </div>
          )}
        </Panel>
      </div>

      {!backendAvailable && (
        <div className="mt-6 border border-red-500/30 bg-[#14161A] p-5">
          <div className="flex items-center gap-3 text-red-200">
            <AlertTriangle className="h-5 w-5" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-red-300">Recovery API unavailable</div>
              <div className="mt-1 text-lg font-semibold text-slate-100">Unable to connect to the recovery service.</div>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <Button type="button" variant="secondary" onClick={() => void onRefresh()}>Retry Connection</Button>
          </div>
        </div>
      )}
    </div>
  )
}
