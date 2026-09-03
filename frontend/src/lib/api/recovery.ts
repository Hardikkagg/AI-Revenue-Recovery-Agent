import type {
  AnalysisResult,
  RecoveryEventInput,
  RecoveryMetricsResponse,
  RecoverySimulationResponse,
} from '../../features/recovery/types/recovery'
import { apiRequest } from './client'

export const recoveryApi = {
  analyze: (payload: RecoveryEventInput) =>
    apiRequest<AnalysisResult>('/recovery/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  simulate: (payload: RecoveryEventInput) =>
    apiRequest<RecoverySimulationResponse>('/recovery/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMetrics: () => apiRequest<RecoveryMetricsResponse>('/recovery/metrics'),
}
