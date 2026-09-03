import { useCallback, useEffect, useMemo, useState } from 'react'

import { recoveryApi } from '../../../lib/api/recovery'
import type {
  AnalysisResult,
  RecoveryEventInput,
  RecoveryMetricsResponse,
  RecoverySimulationResponse,
} from '../types/recovery'

export type PipelineStage = 'DETECT' | 'DIAGNOSE' | 'SCORE' | 'STRATEGY' | 'EXECUTE' | 'OUTCOME' | 'LEARN'

export const scenarioPresets = {
  paymentFailure: {
    customer_id: 1001,
    event_type: 'payment_failure',
    amount: 150,
    payment_method: 'credit_card',
    failure_reason: 'network_error',
    customer_age: 32,
    account_age: 220,
    previous_successes: 12,
    previous_failures: 2,
    retry_count: 1,
    checkout_visits: 0,
    cart_value: 150,
    subscription_age: 0,
  },
  checkoutAbandonment: {
    customer_id: 1002,
    event_type: 'checkout_abandonment',
    amount: 240,
    payment_method: 'credit_card',
    failure_reason: 'cart_abandonment',
    customer_age: 28,
    account_age: 180,
    previous_successes: 8,
    previous_failures: 1,
    retry_count: 0,
    checkout_visits: 4,
    cart_value: 240,
    subscription_age: 0,
  },
  fraudHold: {
    customer_id: 1003,
    event_type: 'payment_failure',
    amount: 500,
    payment_method: 'debit_card',
    failure_reason: 'fraud_hold',
    customer_age: 41,
    account_age: 520,
    previous_successes: 26,
    previous_failures: 1,
    retry_count: 2,
    checkout_visits: 0,
    cart_value: 500,
    subscription_age: 0,
  },
} as const

export function useRecoveryFlow() {
  const [form, setForm] = useState<RecoveryEventInput>({
    ...scenarioPresets.paymentFailure,
    event_id: 9001,
    timestamp: new Date().toISOString(),
  })
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [simulation, setSimulation] = useState<RecoverySimulationResponse | null>(null)
  const [metrics, setMetrics] = useState<RecoveryMetricsResponse | null>(null)
  const [pipelineStage, setPipelineStage] = useState<PipelineStage | null>(null)
  const [loading, setLoading] = useState<'idle' | 'analyzing' | 'simulating'>('idle')
  const [error, setError] = useState<string | null>(null)
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null)

  const applyScenario = useCallback((scenarioName: keyof typeof scenarioPresets) => {
    const next = scenarioPresets[scenarioName]
    setForm({
      ...next,
      event_id: Math.floor(Math.random() * 9000) + 1000,
      timestamp: new Date().toISOString(),
    })
    setAnalysis(null)
    setSimulation(null)
    setPipelineStage(null)
    setError(null)
  }, [])

  const updateField = useCallback((key: keyof RecoveryEventInput, value: string | number | null) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }))
  }, [])

  const refreshMetrics = useCallback(async () => {
    try {
      const metricResponse = await recoveryApi.getMetrics()
      setMetrics(metricResponse)
      setBackendAvailable(true)
      return metricResponse
    } catch (err) {
      setBackendAvailable(false)
      setError(err instanceof Error ? err.message : 'Recovery API unavailable')
      return null
    }
  }, [])

  const runAnalyze = useCallback(async () => {
    setLoading('analyzing')
    setError(null)
    setPipelineStage('DETECT')
    try {
      const payload: RecoveryEventInput = {
        ...form,
        amount: Number(form.amount),
        customer_id: Number(form.customer_id),
        event_id: form.event_id ?? null,
        payment_method: form.payment_method ?? null,
        failure_reason: form.failure_reason ?? null,
        customer_age: form.customer_age ?? null,
        account_age: Number(form.account_age ?? 0),
        previous_successes: Number(form.previous_successes ?? 0),
        previous_failures: Number(form.previous_failures ?? 0),
        retry_count: Number(form.retry_count ?? 0),
        checkout_visits: Number(form.checkout_visits ?? 0),
        cart_value: form.cart_value ?? null,
        subscription_age: Number(form.subscription_age ?? 0),
      }

      const response = await recoveryApi.analyze(payload)
      setAnalysis(response)
      setSimulation(null)
      setPipelineStage('STRATEGY')
      setBackendAvailable(true)
      return response
    } catch (err) {
      setBackendAvailable(false)
      setError(err instanceof Error ? err.message : 'Could not analyze the recovery event.')
      return null
    } finally {
      setLoading('idle')
    }
  }, [form])

  const runSimulate = useCallback(async () => {
    if (!analysis) {
      return null
    }

    setLoading('simulating')
    setError(null)
    setPipelineStage('EXECUTE')

    try {
      const payload: RecoveryEventInput = {
        ...form,
        amount: Number(form.amount),
        customer_id: Number(form.customer_id),
        event_id: form.event_id ?? null,
        payment_method: form.payment_method ?? null,
        failure_reason: form.failure_reason ?? null,
        customer_age: form.customer_age ?? null,
        account_age: Number(form.account_age ?? 0),
        previous_successes: Number(form.previous_successes ?? 0),
        previous_failures: Number(form.previous_failures ?? 0),
        retry_count: Number(form.retry_count ?? 0),
        checkout_visits: Number(form.checkout_visits ?? 0),
        cart_value: form.cart_value ?? null,
        subscription_age: Number(form.subscription_age ?? 0),
      }

      const response = await recoveryApi.simulate(payload)
      setAnalysis(response.analysis)
      setSimulation(response)
      setPipelineStage('LEARN')
      setBackendAvailable(true)
      await refreshMetrics()
      return response
    } catch (err) {
      setBackendAvailable(false)
      setError(err instanceof Error ? err.message : 'Could not execute the recovery strategy.')
      return null
    } finally {
      setLoading('idle')
    }
  }, [analysis, form, refreshMetrics])

  const rewardRatio = useMemo(() => {
    if (!simulation || simulation.simulation.amount_at_risk <= 0) {
      return 0
    }

    return simulation.simulation.recovered_amount / simulation.simulation.amount_at_risk
  }, [simulation])

  useEffect(() => {
    void refreshMetrics()
  }, [refreshMetrics])

  return {
    form,
    analysis,
    simulation,
    metrics,
    pipelineStage,
    loading,
    error,
    backendAvailable,
    rewardRatio,
    updateField,
    applyScenario,
    runAnalyze,
    runSimulate,
    refreshMetrics,
  }
}
