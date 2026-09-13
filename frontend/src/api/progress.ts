import { apiClient } from './client'
import {
  ProgressOverview,
  WeeklyProgress,
  MonthlyProgress,
  VocabularyBreakdown,
} from '@/types'

export const progressApi = {
  getOverview: async (): Promise<ProgressOverview> => {
    const response = await apiClient.get<ProgressOverview>('/progress/overview')
    return response.data
  },

  getWeekly: async (): Promise<WeeklyProgress> => {
    const response = await apiClient.get<WeeklyProgress>('/progress/weekly')
    return response.data
  },

  getMonthly: async (): Promise<MonthlyProgress> => {
    const response = await apiClient.get<MonthlyProgress>('/progress/monthly')
    return response.data
  },

  getVocabularyBreakdown: async (): Promise<VocabularyBreakdown> => {
    const response = await apiClient.get<VocabularyBreakdown>('/progress/vocabulary-breakdown')
    return response.data
  },
}
