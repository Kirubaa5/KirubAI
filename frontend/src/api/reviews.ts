import { apiClient } from './client'
import {
  DueReviewsResponse,
  ReviewSubmitResponse,
  ReviewHistoryResponse,
} from '@/types'

export const reviewsApi = {
  getDue: async (limit: number = 50): Promise<DueReviewsResponse> => {
    const response = await apiClient.get<DueReviewsResponse>('/reviews/due', {
      params: { limit },
    })
    return response.data
  },

  submit: async (
    vocabularyId: string,
    responseText: string,
    reviewType: string = 'recall'
  ): Promise<ReviewSubmitResponse> => {
    const response = await apiClient.post<ReviewSubmitResponse>('/reviews/submit', {
      vocabulary_id: vocabularyId,
      response_text: responseText,
      review_type: reviewType,
    })
    return response.data
  },

  getHistory: async (
    page: number = 1,
    perPage: number = 20,
    vocabularyId?: string
  ): Promise<ReviewHistoryResponse> => {
    const response = await apiClient.get<ReviewHistoryResponse>('/reviews/history', {
      params: {
        page,
        per_page: perPage,
        vocabulary_id: vocabularyId || undefined,
      },
    })
    return response.data
  },
}
