import { apiClient } from './client'
import {
  GamificationOverview,
  AchievementListResponse,
  LevelRoadmapResponse,
} from '@/types'

export const gamificationApi = {
  getOverview: async (): Promise<GamificationOverview> => {
    const response = await apiClient.get<GamificationOverview>('/gamification/overview')
    return response.data
  },

  getAchievements: async (): Promise<AchievementListResponse> => {
    const response = await apiClient.get<AchievementListResponse>('/gamification/achievements')
    return response.data
  },

  getLevels: async (): Promise<LevelRoadmapResponse> => {
    const response = await apiClient.get<LevelRoadmapResponse>('/gamification/levels')
    return response.data
  },
}
