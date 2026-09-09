import { apiClient } from './client'
import { Vocabulary, VocabularyListResponse } from '@/types'

export interface ListVocabularyParams {
  page?: number
  per_page?: number
  status?: string
  search?: string
  sort_by?: string
  order?: 'asc' | 'desc'
}

export const vocabularyApi = {
  list: async (params: ListVocabularyParams = {}): Promise<VocabularyListResponse> => {
    const res = await apiClient.get<VocabularyListResponse>('/vocabulary', { params })
    return res.data
  },
  get: async (id: string): Promise<Vocabulary> => {
    const res = await apiClient.get<Vocabulary>(`/vocabulary/${id}`)
    return res.data
  },
  add: async (word: string): Promise<Vocabulary> => {
    const res = await apiClient.post<Vocabulary>('/vocabulary', { word })
    return res.data
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/vocabulary/${id}`)
  },
  getLearningContent: async (id: string): Promise<Vocabulary> => {
    const res = await apiClient.get<Vocabulary>(`/vocabulary/${id}/learn`)
    return res.data
  },
  markLearned: async (id: string): Promise<Vocabulary> => {
    const res = await apiClient.post<Vocabulary>(`/vocabulary/${id}/mark-learned`)
    return res.data
  },
}
