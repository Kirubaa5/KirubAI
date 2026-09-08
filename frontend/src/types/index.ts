export type VocabularyStatus =
  | 'new'
  | 'learned'
  | 'practiced'
  | 'recalled'
  | 'reinforced'
  | 'mastered'
  | 'struggling'

export interface WordDetails {
  simple_meaning: string
  contextual_meaning?: string
  part_of_speech?: string
  pronunciation_text?: string
  synonyms: string[]
  antonyms: string[]
  word_forms: Record<string, string>
  collocations: string[]
  cefr_level?: string
  difficulty_score?: number
}

export interface VocabularyExample {
  id?: string
  example_text: string
  context_label: string
  order_index: number
}

export interface Vocabulary {
  id: string
  word: string
  status: VocabularyStatus
  mastery_score: number
  practice_count: number
  successful_usage_count: number
  failed_recall_count: number
  last_practiced_at?: string
  last_reviewed_at?: string
  next_review_at?: string
  review_interval_days: number
  created_at: string
  details?: WordDetails
  examples?: VocabularyExample[]
}

export interface VocabularyListResponse {
  items: Vocabulary[]
  total: number
  page: number
  per_page: number
  pages: number
}
