export type RecoveryEventType = 'payment_failure' | 'checkout_abandonment' | 'subscription_failure';

export interface RecoveryEventInput {
  customer_id: number
  event_type: RecoveryEventType | string
  amount: number
  event_id?: number | null
  payment_method?: string | null
  failure_reason?: string | null
  customer_age?: number | null
  account_age?: number
  previous_successes?: number
  previous_failures?: number
  retry_count?: number
  checkout_visits?: number
  cart_value?: number | null
  subscription_age?: number
  timestamp?: string | null
}

export interface DiagnosisResult {
  diagnosis_code: string
  diagnosis_text: string
  recoverability: 'recoverable' | 'potentially_recoverable' | 'unlikely'
  recommended_direction: string
}

export interface LLMGenerationResult {
  provider: string
  model: string
  reasoning: string
  customer_message: string | null
  fallback_used: boolean
  fallback_reason: string | null
}

export interface AnalysisResult {
  event: {
    customer_id: number
    event_id: number | null
    event_type: string
    amount: number
    payment_method: string | null
    failure_reason: string | null
    customer_age: number | null
    account_age: number
    previous_successes: number
    previous_failures: number
    retry_count: number
    checkout_visits: number
    cart_value: number | null
    subscription_age: number
    timestamp: string | null
  }
  detected_event_type: string
  diagnosis: DiagnosisResult
  recovery_probability: number
  confidence: 'LOW' | 'MEDIUM' | 'HIGH'
  recommended_strategy: string
  reasoning: string[]
  score_factors: string[]
  strategy_reason: string
  llm_generation: LLMGenerationResult | null
}

export interface SimulatedGatewayResult {
  gateway_name: string
  action_type: string
  success: boolean
  gateway_reference: string
  response_code: string
  response_message: string
  amount_attempted: number
  amount_settled: number
}

export interface SimulatedCommunicationResult {
  channel: 'email' | 'sms' | 'in_app'
  status: 'simulated_sent' | 'skipped'
  template_name: string
  message: string
  customer_responded: boolean
  response_delay_seconds: number
}

export interface SimulationResult {
  simulation_id: string
  strategy: string
  status: 'completed' | 'escalated' | 'skipped' | 'failed'
  outcome: string
  recovered: boolean
  recovered_amount: number
  amount_at_risk: number
  execution_time_seconds: number
  explanation: string
  action_details: Record<string, unknown>
  gateway_result: SimulatedGatewayResult | null
  communication_result: SimulatedCommunicationResult | null
}

export interface RecoverySimulationResponse {
  analysis: AnalysisResult
  simulation: SimulationResult
}

export interface StrategyPerformance {
  strategy: string
  total_cases: number
  successful_recoveries: number
  failed_cases: number
  recovery_rate: number
  revenue_at_risk: number
  revenue_recovered: number
}

export interface RecoveryMetricsResponse {
  total_cases: number
  resolved_cases: number
  escalated_cases: number
  closed_cases: number
  overall_recovery_rate: number
  total_revenue_at_risk: number
  total_revenue_recovered: number
  strategy_breakdown: StrategyPerformance[]
  feedback_samples_count: number
}
