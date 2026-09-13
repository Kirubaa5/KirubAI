import { apiClient } from './client'
import {
  LearningProfile,
  PersonalizedRecommendationsResponse,
  GeneratePersonalizedScenarioRequest,
  PersonalizedScenario,
} from '@/types'

export const personalizationApi = {
  getProfile: async (): Promise<LearningProfile> => {
    const response = await apiClient.get<LearningProfile>('/personalization/profile')
    return response.data
  },

  getRecommendations: async (limit: number = 5): Promise<PersonalizedRecommendationsResponse> => {
    const response = await apiClient.get<PersonalizedRecommendationsResponse>(
      '/personalization/recommendations',
      {
        params: { limit },
      }
    )
    return response.data
  },

  generateScenario: async (
    data: GeneratePersonalizedScenarioRequest
  ): Promise<PersonalizedScenario> => {
    const response = await apiClient.post<PersonalizedScenario>(
      '/personalization/scenarios/generate',
      data
    )
    return response.data
  },
}
