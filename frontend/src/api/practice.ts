import { apiClient } from './client'
import {
  PracticeStartResponse,
  PracticeSubmitResponse,
  PracticeSession,
  PracticeSessionListResponse,
  Scenario,
  MultiWordStartResponse,
  MultiWordAttemptResponse,
  MultiWordSessionResponse,
  MultiWordSessionListResponse,
  MultiWordEligibleResponse,
} from '@/types'

export interface ListPracticeParams {
  vocabulary_id?: string
  page?: number
  per_page?: number
}

export const practiceApi = {
  start: async (vocabularyId: string, sessionType = 'scenario'): Promise<PracticeStartResponse> => {
    const res = await apiClient.post<PracticeStartResponse>('/practice/start', {
      vocabulary_id: vocabularyId,
      session_type: sessionType,
    })
    return res.data
  },

  getScenario: async (sessionId: string): Promise<Scenario> => {
    const res = await apiClient.post<Scenario>(`/practice/${sessionId}/scenario`)
    return res.data
  },

  submit: async (
    sessionId: string,
    scenarioText: string,
    response: string
  ): Promise<PracticeSubmitResponse> => {
    const res = await apiClient.post<PracticeSubmitResponse>(`/practice/${sessionId}/submit`, {
      scenario_text: scenarioText,
      response,
    })
    return res.data
  },

  getSession: async (sessionId: string): Promise<PracticeSession> => {
    const res = await apiClient.get<PracticeSession>(`/practice/${sessionId}`)
    return res.data
  },

  listSessions: async (params: ListPracticeParams = {}): Promise<PracticeSessionListResponse> => {
    const res = await apiClient.get<PracticeSessionListResponse>('/practice/sessions', {
      params,
    })
    return res.data
  },

  complete: async (sessionId: string): Promise<PracticeSession> => {
    const res = await apiClient.post<PracticeSession>(`/practice/${sessionId}/complete`)
    return res.data
  },

  // Multi-Word Practice ("Use My Vocabulary")
  getMultiWordEligible: async (): Promise<MultiWordEligibleResponse> => {
    const res = await apiClient.get<MultiWordEligibleResponse>('/practice/multi-word/eligible')
    return res.data
  },

  startMultiWord: async (vocabularyIds?: string[]): Promise<MultiWordStartResponse> => {
    const res = await apiClient.post<MultiWordStartResponse>('/practice/multi-word', {
      vocabulary_ids: vocabularyIds && vocabularyIds.length > 0 ? vocabularyIds : undefined,
    })
    return res.data
  },

  submitMultiWord: async (sessionId: string, response: string): Promise<MultiWordAttemptResponse> => {
    const res = await apiClient.post<MultiWordAttemptResponse>(`/practice/multi-word/${sessionId}/submit`, {
      response,
    })
    return res.data
  },

  getMultiWordSession: async (sessionId: string): Promise<MultiWordSessionResponse> => {
    const res = await apiClient.get<MultiWordSessionResponse>(`/practice/multi-word/${sessionId}`)
    return res.data
  },

  listMultiWordSessions: async (page = 1, perPage = 20): Promise<MultiWordSessionListResponse> => {
    const res = await apiClient.get<MultiWordSessionListResponse>('/practice/multi-word/sessions', {
      params: { page, per_page: perPage },
    })
    return res.data
  },
}

