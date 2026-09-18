import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AdaptiveLearningPage } from '@/pages/AdaptiveLearningPage'
import { adaptiveApi } from '@/api/adaptive'
import { AdaptivePlanResponse } from '@/types'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/api/adaptive', () => ({
  adaptiveApi: {
    getPlan: vi.fn(),
  },
}))

const mockActivePlanData: AdaptivePlanResponse = {
  generated_at: '2026-09-18T10:00:00Z',
  learner_profile: {
    cefr_level: 'B2',
    difficulty_score: 6.5,
    average_mastery: 0.58,
    total_vocabulary: 12,
    active_vocabulary: 8,
    mastered_count: 3,
    struggling_count: 1,
    recent_accuracy_rate: 0.85,
    practice_success_rate: 0.88,
    recall_accuracy_rate: 0.82,
  },
  primary_recommendation: {
    id: 'rec_due_reviews_1',
    activity_type: 'review',
    title: 'Due Spaced Reviews (2 words)',
    reason: 'You have 2 spaced repetition reviews due today according to the forgetting curve.',
    learning_objective: 'Prevent forgetting curve decay through active retrieval and contextual recall.',
    target_words: ['hesitate', 'vividly'],
    target_vocabulary_ids: ['uuid-1', 'uuid-2'],
    difficulty: 6.5,
    cefr_level: 'B2',
    priority: 'urgent',
    action_url: '/reviews',
    action_label: 'Start Spaced Reviews',
  },
  recommendations: [
    {
      id: 'rec_due_reviews_1',
      activity_type: 'review',
      title: 'Due Spaced Reviews (2 words)',
      reason: 'You have 2 spaced repetition reviews due today according to the forgetting curve.',
      learning_objective: 'Prevent forgetting curve decay through active retrieval and contextual recall.',
      target_words: ['hesitate', 'vividly'],
      target_vocabulary_ids: ['uuid-1', 'uuid-2'],
      difficulty: 6.5,
      cefr_level: 'B2',
      priority: 'urgent',
      action_url: '/reviews',
      action_label: 'Start Spaced Reviews',
    },
    {
      id: 'rec_struggling_2',
      activity_type: 'practice',
      title: "Struggling Word Remediation: 'reluctant'",
      reason: "Word 'reluctant' has 2 failed recalls. Targeted scenario practice will restore confidence.",
      learning_objective: "Apply 'reluctant' in a structured real-world scenario to overcome hesitation and elevate mastery.",
      target_words: ['reluctant'],
      target_vocabulary_ids: ['uuid-3'],
      difficulty: 5.7,
      cefr_level: 'B2',
      priority: 'high',
      action_url: '/practice/uuid-3',
      action_label: "Practice 'reluctant'",
    },
    {
      id: 'rec_multi_word_3',
      activity_type: 'multi_word',
      title: 'Multi-Word Vocabulary Synthesis',
      reason: 'You have 4 active words ready to be synthesized into a single contextual narrative.',
      learning_objective: 'Synthesize multiple target words simultaneously within one realistic communication scenario.',
      target_words: ['hesitate', 'vividly', 'resilient'],
      target_vocabulary_ids: ['uuid-1', 'uuid-2', 'uuid-4'],
      difficulty: 7.0,
      cefr_level: 'B2',
      priority: 'medium',
      action_url: '/practice/multi-word',
      action_label: 'Synthesize Vocabulary',
    },
  ],
  diagnostic_focus: {
    primary_weakness: 'Collocation precision & patterns',
    recommended_strategy: 'Prioritize contextual application that reinforces correct collocation rules.',
    recent_error_count: 3,
    top_error_types: [
      {
        error_type: 'collocation',
        count: 2,
        description: 'Preposition pairings, natural word combinations, and idioms.',
        sample_phrases: ['hesitate of doing', 'make hesitation'],
      },
      {
        error_type: 'grammar',
        count: 1,
        description: 'Sentence construction, tense consistency, and subject-verb agreements.',
        sample_phrases: ['he hesitate yesterday'],
      },
    ],
  },
  daily_plan_sync: {
    daily_goal_progress: 3,
    daily_goal_target: 5,
    is_goal_completed: false,
    current_streak: 4,
  },
}

const mockEmptyPlanData: AdaptivePlanResponse = {
  generated_at: '2026-09-18T10:00:00Z',
  learner_profile: {
    cefr_level: 'A2',
    difficulty_score: 2.5,
    average_mastery: 0.0,
    total_vocabulary: 0,
    active_vocabulary: 0,
    mastered_count: 0,
    struggling_count: 0,
    recent_accuracy_rate: 0.7,
    practice_success_rate: 0.7,
    recall_accuracy_rate: 0.7,
  },
  primary_recommendation: {
    id: 'rec_empty_welcome',
    activity_type: 'learn',
    title: 'Add Your First Vocabulary Words',
    reason: 'Your vocabulary bank is currently empty. Adding words unlocks personalized scenario practice and spaced repetition.',
    learning_objective: 'Select 3-5 target English words to begin your active vocabulary journey.',
    target_words: ['hesitate', 'resilient', 'eloquent'],
    target_vocabulary_ids: [],
    difficulty: 2.5,
    cefr_level: 'A2',
    priority: 'high',
    action_url: '/vocabulary',
    action_label: 'Explore & Add Words',
  },
  recommendations: [],
  diagnostic_focus: {
    primary_weakness: null,
    recommended_strategy: 'Add your initial target vocabulary to establish your baseline learning profile.',
    recent_error_count: 0,
    top_error_types: [],
  },
  daily_plan_sync: {
    daily_goal_progress: 0,
    daily_goal_target: 5,
    is_goal_completed: false,
    current_streak: 0,
  },
}

function renderAdaptivePage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdaptiveLearningPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AdaptiveLearningPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading spinner initially while fetching plan', () => {
    vi.mocked(adaptiveApi.getPlan).mockReturnValueOnce(new Promise(() => {}))
    renderAdaptivePage()
    expect(screen.getByText(/analyzing performance metrics/i)).toBeInTheDocument()
  })

  it('renders error state when API call fails', async () => {
    vi.mocked(adaptiveApi.getPlan).mockRejectedValueOnce(new Error('Network error'))
    renderAdaptivePage()

    await waitFor(() => {
      expect(screen.getByText('Could Not Load Adaptive Plan')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  it('renders empty state when learner has zero vocabulary words', async () => {
    vi.mocked(adaptiveApi.getPlan).mockResolvedValueOnce(mockEmptyPlanData)
    renderAdaptivePage()

    await waitFor(() => {
      expect(screen.getByText('Adaptive Learning Plan')).toBeInTheDocument()
      expect(screen.getByText('Welcome to Adaptive Learning')).toBeInTheDocument()
      expect(screen.getByText(/your vocabulary bank is currently empty/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add first words/i })).toBeInTheDocument()
    })
  })

  it('renders full adaptive learning plan with primary recommendation and metrics', async () => {
    vi.mocked(adaptiveApi.getPlan).mockResolvedValueOnce(mockActivePlanData)
    renderAdaptivePage()

    await waitFor(() => {
      // Header & Profile
      expect(screen.getByText('Adaptive Learning Plan')).toBeInTheDocument()
      expect(screen.getAllByText(/CEFR B2/).length).toBeGreaterThan(0)
      expect(screen.getByText('Diff: 6.5 / 10.0')).toBeInTheDocument()
      expect(screen.getByText(/58%/)).toBeInTheDocument()
      expect(screen.getByText('8 Active Words')).toBeInTheDocument()

      // Daily Sync Stats
      expect(screen.getByText('3 / 5 Activities')).toBeInTheDocument()
      expect(screen.getByText('4 Days')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()

      // Primary Hero Recommendation
      expect(screen.getByText('Recommended Next Activity')).toBeInTheDocument()
      expect(screen.getAllByText('Due Spaced Reviews (2 words)').length).toBeGreaterThan(0)
      expect(screen.getAllByText(/you have 2 spaced repetition reviews due today/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/prevent forgetting curve decay through active retrieval/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText('hesitate').length).toBeGreaterThan(0)
      expect(screen.getAllByText('vividly').length).toBeGreaterThan(0)
      expect(screen.getAllByRole('button', { name: /start spaced reviews/i }).length).toBeGreaterThan(0)
    })
  })

  it('renders diagnostic focus and error breakdown', async () => {
    vi.mocked(adaptiveApi.getPlan).mockResolvedValueOnce(mockActivePlanData)
    renderAdaptivePage()

    await waitFor(() => {
      expect(screen.getByText('Diagnostic Focus & Linguistic Analysis')).toBeInTheDocument()
      expect(screen.getByText('Collocation precision & patterns')).toBeInTheDocument()
      expect(screen.getByText(/prioritize contextual application that reinforces correct collocation rules/i)).toBeInTheDocument()
      expect(screen.getByText(/recent error patterns \(3 detected\)/i)).toBeInTheDocument()
      expect(screen.getByText('collocation')).toBeInTheDocument()
      expect(screen.getByText('grammar')).toBeInTheDocument()
      expect(screen.getByText('"hesitate of doing"')).toBeInTheDocument()
    })
  })

  it('renders prioritized adaptive queue and allows action navigation', async () => {
    const user = userEvent.setup()
    vi.mocked(adaptiveApi.getPlan).mockResolvedValueOnce(mockActivePlanData)
    renderAdaptivePage()

    await waitFor(() => {
      expect(screen.getByText('Prioritized Adaptive Queue')).toBeInTheDocument()
      expect(screen.getByText("Struggling Word Remediation: 'reluctant'")).toBeInTheDocument()
      expect(screen.getByText('Multi-Word Vocabulary Synthesis')).toBeInTheDocument()
    })

    const practiceButton = screen.getByRole('button', { name: /practice 'reluctant'/i })
    expect(practiceButton).toBeInTheDocument()
    await user.click(practiceButton)

    expect(mockNavigate).toHaveBeenCalledWith('/practice/uuid-3')
  })
})
