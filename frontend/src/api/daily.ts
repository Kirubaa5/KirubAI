import { apiClient } from './client'
import { DailyPlanResponse } from '../types'

export const dailyApi = {
  getDailyPlan: async (): Promise<DailyPlanResponse> => {
    const res = await apiClient.get<DailyPlanResponse>('/daily/plan')
    return res.data
  },
}
