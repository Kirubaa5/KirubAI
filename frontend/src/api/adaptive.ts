import { apiClient } from './client'
import { AdaptivePlanResponse } from '@/types'

export const adaptiveApi = {
  /**
   * Fetch the comprehensive adaptive learning plan.
   */
  getPlan: async (): Promise<AdaptivePlanResponse> => {
    const response = await apiClient.get<AdaptivePlanResponse>('/adaptive/plan')
    return response.data
  },
}
