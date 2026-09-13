import { apiClient } from './client'
import { DashboardSummary } from '@/types'

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/dashboard')
    return response.data
  },
}
