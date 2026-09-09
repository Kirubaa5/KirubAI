import { apiClient } from './client'
import {
  PracticeStartResponse,
  PracticeSubmitResponse,
  PracticeSession,
  PracticeSessionListResponse,
  Scenario,
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
}
