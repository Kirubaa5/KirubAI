import { apiClient } from './client'
import {
  ConversationStartRequest,
  ConversationStartResponse,
  ConversationMessageResponse,
  ConversationEndResponse,
  ConversationSession,
  ConversationListResponse,
} from '@/types'

export const conversationsApi = {
  start: async (data?: ConversationStartRequest): Promise<ConversationStartResponse> => {
    const response = await apiClient.post<ConversationStartResponse>(
      '/conversations/start',
      data || {}
    )
    return response.data
  },

  sendMessage: async (
    sessionId: string,
    content: string
  ): Promise<ConversationMessageResponse> => {
    const response = await apiClient.post<ConversationMessageResponse>(
      `/conversations/${sessionId}/message`,
      { content }
    )
    return response.data
  },

  end: async (sessionId: string): Promise<ConversationEndResponse> => {
    const response = await apiClient.post<ConversationEndResponse>(
      `/conversations/${sessionId}/end`
    )
    return response.data
  },

  getById: async (sessionId: string): Promise<ConversationSession> => {
    const response = await apiClient.get<ConversationSession>(
      `/conversations/${sessionId}`
    )
    return response.data
  },

  list: async (
    page: number = 1,
    perPage: number = 20
  ): Promise<ConversationListResponse> => {
    const response = await apiClient.get<ConversationListResponse>(
      '/conversations',
      {
        params: {
          page,
          per_page: perPage,
        },
      }
    )
    return response.data
  },
}
