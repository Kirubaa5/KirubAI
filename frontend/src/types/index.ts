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

// Phase 12: Advanced AI Evaluation & Error Analysis Types
export type DiagnosticErrorType = 'grammar' | 'collocation' | 'semantic' | 'tone' | 'spelling' | string
export type DiagnosticSeverity = 'low' | 'medium' | 'high' | string

export interface DiagnosticError {
  error_type: DiagnosticErrorType
  original_text: string
  explanation: string
  suggested_correction: string
  severity: DiagnosticSeverity
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
  errors?: DiagnosticError[]
  cefr_level?: string
  actionable_tips?: string[]
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
  errors?: DiagnosticError[]
  cefr_level?: string
  actionable_tips?: string[]
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

// Phase 6: AI Text Conversation Coach Types
export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  vocabulary_detected: string[]
  order_index: number
  created_at: string
}

export interface VocabularyUsageDetail {
  word: string
  used: boolean
  quality?: number
  context?: string
}

export interface ConversationEvaluation {
  vocabulary_used: string[]
  vocabulary_missed: string[]
  usage_quality: Record<string, number>
  overall_fluency: number
  feedback: string
  vocabulary_details?: VocabularyUsageDetail[]
  errors?: DiagnosticError[]
  cefr_level?: string
  actionable_tips?: string[]
}

export interface ConversationStartRequest {
  topic?: string
  use_vocabulary?: boolean
  target_words?: string[]
}

export interface ConversationStartResponse {
  session_id: string
  topic: string
  initial_message: string
  target_vocabulary: string[]
}

export interface ConversationMessageResponse {
  message_id: string
  response: string
  vocabulary_detected: string[]
  vocabulary_used: string[]
}

export interface ConversationEndResponse {
  session_id: string
  status: string
  xp_earned: number
  evaluation: ConversationEvaluation
}

export interface ConversationSession {
  id: string
  user_id?: string
  topic?: string
  target_vocabulary: string[]
  vocabulary_used: string[]
  vocabulary_usage_count: number
  status: 'active' | 'ended'
  message_count: number
  evaluation?: ConversationEvaluation
  started_at: string
  ended_at?: string
  messages?: ConversationMessage[]
}

export interface ConversationListResponse {
  items: ConversationSession[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Phase 7: Personalized Learning Engine Types
export interface WordSummaryItem {
  id: string
  word: string
  status: VocabularyStatus
  mastery_score: number
  practice_count: number
  successful_usage_count: number
  failed_recall_count: number
  next_review_at?: string
}

export interface MasteryDistribution {
  new: number
  learned: number
  practiced: number
  recalled: number
  reinforced: number
  mastered: number
  struggling: number
  total: number
}

export interface LearningProfile {
  total_vocabulary: number
  active_vocabulary: number
  mastered_count: number
  struggling_count: number
  average_mastery: number
  mastery_distribution: MasteryDistribution
  weak_words: WordSummaryItem[]
  strong_words: WordSummaryItem[]
  total_practice_attempts: number
  practice_success_rate: number
  total_reviews_completed: number
  recall_accuracy_rate: number
  total_conversations_completed: number
  adaptive_cefr_level: string
  adaptive_difficulty_score: number
  recommended_focus: string
}

export interface PersonalizedRecommendation {
  vocabulary_id?: string
  word: string
  activity_type: 'review' | 'practice' | 'conversation' | 'learn'
  priority: 'high' | 'medium' | 'low'
  reason: string
  recommended_difficulty: number
  cefr_level: string
}

export interface PersonalizedRecommendationsResponse {
  recommendations: PersonalizedRecommendation[]
  total_due_reviews: number
  total_struggling_words: number
  recommended_daily_focus: string
  learner_level: string
}

export interface GeneratePersonalizedScenarioRequest {
  word: string
  domain?: string
  weak_area_context?: string
  target_cefr_level?: string
}

export interface PersonalizedScenario {
  vocabulary_id?: string
  word: string
  situation: string
  prompt: string
  context_hint?: string
  domain: string
  cefr_level: string
  difficulty_score: number
}

// Phase 8: RAG Knowledge System Types
export type KnowledgeCategory = 'grammar' | 'common_mistakes' | 'collocations' | 'learning_tips' | 'all'

export interface KnowledgeDocument {
  id: string
  title: string
  category: string
  topic: string
  content: string
  summary: string
  tags: string[]
  rules: string[]
  correct_examples: string[]
  common_mistakes: string[]
  source: string
}

export interface KnowledgeSourceItem {
  id: string
  title: string
  category: string
  topic: string
  relevance_score: number
  summary: string
  source: string
}

export interface KnowledgeExplanationResponse {
  query: string
  category?: string
  target_word?: string
  summary: string
  detailed_explanation: string
  rule_applied: string
  correct_usage: string[]
  incorrect_usage: string[]
  learning_tip: string
  groundedness_confidence: number
  sources: KnowledgeSourceItem[]
}

export interface KnowledgeQueryRequest {
  query: string
  category?: string
  target_word?: string
  top_k?: number
}

export interface KnowledgeCategoryResponse {
  categories: Record<string, string[]>
  total_documents: number
}

export interface KnowledgeDocumentListResponse {
  items: KnowledgeDocument[]
  total: number
}

// Phase 9: Progress & Analytics Dashboard Types
export interface WordOfTheDay {
  word: string
  meaning: string
  cefr_level?: string
  part_of_speech?: string
  example_sentence?: string
}

export interface DashboardToday {
  reviews_due: number
  words_to_practice: number
  daily_goal_progress: number
  daily_goal_target: number
  word_of_the_day?: WordOfTheDay
}

export interface DashboardStats {
  total_words: number
  mastered_words: number
  active_words: number
  struggling_words: number
  current_streak: number
  total_xp: number
  level: number
}

export interface DashboardRecentActivityItem {
  type: 'practice' | 'review' | 'conversation' | 'vocabulary' | string
  word?: string
  score?: number
  result?: string
  at: string
  detail?: string
}

export interface DashboardSummary {
  today: DashboardToday
  stats: DashboardStats
  recent_activity: DashboardRecentActivityItem[]
}

export interface VocabularyBreakdownItem {
  status: string
  count: number
  percentage: number
}

export interface MasteryBracketItem {
  bracket: string
  count: number
  percentage: number
}

export interface VocabularyBreakdown {
  total_words: number
  by_status: VocabularyBreakdownItem[]
  by_mastery_bracket: MasteryBracketItem[]
  by_cefr_level: Record<string, number>
}

export interface DailyProgressItem {
  date: string
  day_name: string
  practices_count: number
  reviews_count: number
  conversations_count: number
  words_added: number
  words_mastered: number
  accuracy_rate: number
  xp_earned: number
}

export interface WeeklyProgress {
  daily_progress: DailyProgressItem[]
  total_practices: number
  total_reviews: number
  total_conversations: number
  total_words_added: number
  total_xp_earned: number
  average_accuracy_rate: number
  active_days: number
}

export interface MonthlyTrendItem {
  date: string
  day_or_week: string
  activities_count: number
  words_acquired: number
  accuracy_rate: number
  xp_earned: number
}

export interface MonthlyProgress {
  trends: MonthlyTrendItem[]
  total_activities: number
  words_learned: number
  average_accuracy_rate: number
  active_days: number
  retention_rate: number
}

export interface ProgressOverview {
  total_vocabulary: number
  active_vocabulary: number
  mastered_count: number
  struggling_count: number
  average_mastery: number
  total_practice_attempts: number
  practice_accuracy: number
  average_practice_score: number
  total_reviews_completed: number
  recall_accuracy_rate: number
  total_conversations: number
  vocabulary_used_in_conversations: number
  current_streak: number
  longest_streak: number
  total_xp: number
  level: number
  daily_goal: number
}

// Phase 10: Gamification & Achievements Types
export interface LevelInfo {
  level: number
  title: string
  total_xp: number
  current_level_xp: number
  next_level_xp: number
  xp_within_level: number
  xp_required_for_next_level: number
  progress_percentage: number
}

export interface LevelRoadmapItem {
  level: number
  title: string
  xp_required: number
  is_unlocked: boolean
  is_current: boolean
}

export interface LevelRoadmapResponse {
  current_level: number
  current_xp: number
  level_title: string
  current_level_xp: number
  next_level_xp: number
  xp_within_level: number
  progress_percentage: number
  levels: LevelRoadmapItem[]
}

export interface Achievement {
  key: string
  title: string
  description: string
  category: 'vocabulary' | 'practice' | 'reviews' | 'conversations' | 'streaks' | string
  icon: string
  target_threshold: number
  current_progress: number
  progress_percentage: number
  is_unlocked: boolean
  achieved_at?: string
}

export interface AchievementListResponse {
  total: number
  unlocked_count: number
  completion_percentage: number
  items: Achievement[]
}

export interface GamificationOverview {
  level: number
  level_title: string
  total_xp: number
  current_level_xp: number
  next_level_xp: number
  xp_within_level: number
  xp_required_for_next_level: number
  level_progress_percentage: number
  current_streak: number
  longest_streak: number
  daily_goal: number
  daily_goal_progress: number
  is_daily_goal_completed: boolean
  unlocked_achievements_count: number
  total_achievements_count: number
  achievement_completion_percentage: number
  recent_achievements: Achievement[]
  next_achievements: Achievement[]
}

// Phase 11: Daily Learning System & "Use My Vocabulary" Types
export interface DailyTaskItem {
  id: string
  priority: number
  task_type: 'reviews_due' | 'struggling_practice' | 'learn_new' | 'use_my_vocabulary' | string
  title: string
  description: string
  status: 'pending' | 'completed' | 'ready' | 'locked' | string
  item_count: number
  action_label: string
  action_url: string
  items?: Array<{
    id: string
    word: string
    status?: string
    mastery_score?: number
    practice_count?: number
    review_interval_days?: number
  }>
}

export interface DailyPlanResponse {
  date: string
  daily_goal_target: number
  daily_goal_progress: number
  is_goal_completed: boolean
  current_streak: number
  word_of_the_day?: WordOfTheDay
  tasks: DailyTaskItem[]
  completed_tasks_count: number
  total_tasks_count: number
  completion_percentage: number
}

export interface MultiWordTargetWord {
  id: string
  word: string
  meaning?: string
  cefr_level?: string
  status: VocabularyStatus | string
}

export interface MultiWordStartRequest {
  vocabulary_ids?: string[]
}

export interface MultiWordStartResponse {
  session_id: string
  target_words: MultiWordTargetWord[]
  scenario: Scenario
  created_at: string
}

export interface MultiWordSubmitRequest {
  response: string
}

export interface WordEvaluationDetail {
  word: string
  used: boolean
  used_correctly: boolean
  used_naturally: boolean
  score?: number
  feedback: string
}

export interface MultiWordAttemptResponse {
  id: string
  session_id: string
  user_response: string
  scores: PracticeScores
  word_evaluations: WordEvaluationDetail[]
  feedback: string
  improved_version?: string
  is_successful: boolean
  errors?: DiagnosticError[]
  cefr_level?: string
  actionable_tips?: string[]
  xp_earned: number
  created_at: string
}

export interface MultiWordSessionResponse {
  id: string
  user_id: string
  target_words: string[]
  target_vocabulary_ids: string[]
  scenario_text: string
  scenario_prompt: string
  context_hint?: string
  status: 'active' | 'completed' | string
  total_attempts: number
  successful_attempts: number
  average_score?: number
  started_at: string
  completed_at?: string
  attempts: MultiWordAttemptResponse[]
}

export interface MultiWordEligibleResponse {
  eligible_count: number
  total_words: number
  min_required: number
  is_eligible: boolean
  items: MultiWordTargetWord[]
}

export interface MultiWordSessionListResponse {
  items: MultiWordSessionResponse[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Phase 13: Export, Data Portability & Study Deck Generator Types
export type ExportFormat = 'anki' | 'csv' | 'json'

export interface ExportFilterParams {
  format?: ExportFormat | 'anki_tsv' | 'anki_csv'
  status?: string
  cefr_level?: string
  min_mastery?: number
  max_mastery?: number
  date_from?: string
  date_to?: string
  sort_by?: string
  order?: 'asc' | 'desc'
  include_examples?: boolean
  include_learning_stats?: boolean
}

export interface ExportPreviewResponse {
  total_vocabulary_count: number
  matching_words_count: number
  status_distribution: Record<string, number>
  cefr_distribution: Record<string, number>
  sample_words: string[]
}

