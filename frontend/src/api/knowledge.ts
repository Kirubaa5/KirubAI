import { apiClient } from './client'
import {
  KnowledgeQueryRequest,
  KnowledgeExplanationResponse,
  KnowledgeCategoryResponse,
  KnowledgeDocumentListResponse,
  KnowledgeDocument,
} from '@/types'

export const knowledgeApi = {
  queryKnowledge: async (data: KnowledgeQueryRequest): Promise<KnowledgeExplanationResponse> => {
    const response = await apiClient.post<KnowledgeExplanationResponse>('/knowledge/query', data)
    return response.data
  },

  getCategories: async (): Promise<KnowledgeCategoryResponse> => {
    const response = await apiClient.get<KnowledgeCategoryResponse>('/knowledge/categories')
    return response.data
  },

  getDocuments: async (params?: { category?: string; search?: string }): Promise<KnowledgeDocumentListResponse> => {
    const response = await apiClient.get<KnowledgeDocumentListResponse>('/knowledge/documents', {
      params,
    })
    return response.data
  },

  getDocumentById: async (docId: string): Promise<KnowledgeDocument> => {
    const response = await apiClient.get<KnowledgeDocument>(`/knowledge/documents/${docId}`)
    return response.data
  },
}
