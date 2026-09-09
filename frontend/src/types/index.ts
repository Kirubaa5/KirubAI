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

// Phase 4: Practice Engine Types
export interface Scenario {
  situation: string
  prompt: string
  context_hint?: string
}

export interface PracticeScores {
  vocabulary_usage: number
  grammar: number
  context: number
  naturalness: number
  overall: number
}

export interface PracticeAttempt {
  id: string
  session_id: string
  vocabulary_id: string
  target_word: string
  scenario_text: string
  user_response: string
  scores: PracticeScores
  feedback: string
  improved_version?: string
  is_successful: boolean
  created_at: string
}

export interface PracticeStartResponse {
  session_id: string
  vocabulary_id: string
  target_word: string
  scenario: Scenario
}

export interface PracticeSubmitResponse {
  attempt_id: string
  session_id: string
  vocabulary_id: string
  target_word: string
  scenario_text: string
  user_response: string
  scores: PracticeScores
  feedback: string
  improved_version?: string
  is_successful: boolean
  can_continue: boolean
  next_scenario?: Scenario
}

export interface PracticeSession {
  id: string
  user_id: string
  vocabulary_id: string
  target_word?: string
  session_type: string
  status: string
  total_attempts: number
  successful_attempts: number
  average_score?: number
  started_at: string
  completed_at?: string
  attempts: PracticeAttempt[]
}

export interface PracticeSessionListResponse {
  items: PracticeSession[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Phase 5: Spaced Repetition & Review Types
export interface ReviewPrompt {
  prompt_type: string
  definition?: string
  part_of_speech?: string
  cloze_sentence?: string
  hint?: string
  context_label?: string
  synonyms_hint?: string[]
}

export interface DueReviewItem {
  vocabulary_id: string
  word: string
  status: VocabularyStatus
  mastery_score: number
  last_reviewed_at?: string
  next_review_at?: string
  review_interval_days: number
  review_type: string
  prompt: ReviewPrompt
}

export interface DueReviewsResponse {
  due_count: number
  items: DueReviewItem[]
}

export interface ReviewSubmitResponse {
  recall_successful: boolean
  score: number
  feedback: string
  previous_status: VocabularyStatus
  new_status: VocabularyStatus
  previous_interval_days: number
  new_interval_days: number
  next_review_at: string
  mastery_score: number
  xp_earned: number
  target_word: string
}

export interface ReviewRecord {
  id: string
  user_id: string
  vocabulary_id: string
  target_word?: string
  review_type: string
  recall_successful: boolean
  response_text?: string
  score?: number
  feedback?: string
  previous_interval_days: number
  new_interval_days: number
  previous_status: VocabularyStatus
  new_status: VocabularyStatus
  reviewed_at: string
}

export interface ReviewHistoryResponse {
  items: ReviewRecord[]
  total: number
  page: number
  per_page: number
  pages: number
}

