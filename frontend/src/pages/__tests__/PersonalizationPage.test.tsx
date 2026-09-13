import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PersonalizationPage } from '@/pages/PersonalizationPage'
import { personalizationApi } from '@/api/personalization'
import {
  LearningProfile,
  PersonalizedRecommendationsResponse,
  PersonalizedScenario,
} from '@/types'

vi.mock('@/api/personalization', () => ({
  personalizationApi: {
    getProfile: vi.fn(),
    getRecommendations: vi.fn(),
    generateScenario: vi.fn(),
  },
}))

const mockProfile: LearningProfile = {
  total_vocabulary: 12,
  active_vocabulary: 8,
  mastered_count: 2,
  struggling_count: 2,
  average_mastery: 0.65,
  mastery_distribution: {
    new: 2,
    learned: 2,
    practiced: 2,
    recalled: 2,
    reinforced: 0,
    mastered: 2,
    struggling: 2,
    total: 12,
  },
  weak_words: [
    {
      id: 'vocab-1',
      word: 'hesitate',
      status: 'struggling',
      mastery_score: 0.25,
      practice_count: 3,
      successful_usage_count: 1,
      failed_recall_count: 2,
    },
    {
      id: 'vocab-2',
      word: 'reluctant',
      status: 'struggling',
      mastery_score: 0.3,
      practice_count: 2,
      successful_usage_count: 0,
      failed_recall_count: 1,
    },
  ],
  strong_words: [
    {
      id: 'vocab-3',
      word: 'confident',
      status: 'mastered',
      mastery_score: 0.95,
      practice_count: 6,
      successful_usage_count: 6,
      failed_recall_count: 0,
    },
  ],
  total_practice_attempts: 10,
  practice_success_rate: 0.8,
  total_reviews_completed: 6,
  recall_accuracy_rate: 0.85,
  total_conversations_completed: 3,
  adaptive_cefr_level: 'B2',
  adaptive_difficulty_score: 6.2,
  recommended_focus: 'Spaced Repetition: You have 2 reviews due today to prevent memory decay.',
}

const mockRecommendationsResponse: PersonalizedRecommendationsResponse = {
  recommendations: [
    {
      vocabulary_id: 'vocab-1',
      word: 'hesitate',
      activity_type: 'practice',
      priority: 'high',
      reason: 'Word is marked as struggling. Targeted scenario practice will strengthen retention.',
      recommended_difficulty: 5.2,
      cefr_level: 'B2',
    },
    {
      vocabulary_id: 'vocab-3',
      word: 'confident',
      activity_type: 'conversation',
      priority: 'medium',
      reason: 'Use in natural AI conversation to advance towards full mastery.',
      recommended_difficulty: 6.7,
      cefr_level: 'B2',
    },
  ],
  total_due_reviews: 0,
  total_struggling_words: 2,
  recommended_daily_focus: 'Targeted Reinforcement: Focus on mastering your 2 struggling words.',
  learner_level: 'B2 (Difficulty 6.2/10)',
}

const mockGeneratedScenario: PersonalizedScenario = {
  vocabulary_id: 'vocab-1',
  word: 'hesitate',
  situation: 'During a quarterly team sync, your project manager asks if your team can take on a client feature by Friday.',
  prompt: 'Politely convey your hesitation regarding the deadline using the word "hesitate".',
  context_hint: 'Be constructive and offer to re-evaluate milestone priorities.',
  domain: 'Workplace & Business',
  cefr_level: 'B2',
  difficulty_score: 6.2,
}

function renderPersonalizationPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/personalization']}>
        <Routes>
          <Route path="/personalization" element={<PersonalizationPage />} />
          <Route path="/practice/:id" element={<div>Practice Page Mock</div>} />
          <Route path="/reviews" element={<div>Reviews Page Mock</div>} />
          <Route path="/conversations" element={<div>Conversations Page Mock</div>} />
          <Route path="/vocabulary" element={<div>Vocabulary Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PersonalizationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders learning profile, CEFR badge, and recommendation cards', async () => {
    vi.mocked(personalizationApi.getProfile).mockResolvedValueOnce(mockProfile)
    vi.mocked(personalizationApi.getRecommendations).mockResolvedValueOnce(mockRecommendationsResponse)

    renderPersonalizationPage()

    await waitFor(() => {
      expect(screen.getByText(/personalized learning plan/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/cefr b2/i)).toBeInTheDocument()
    expect(screen.getByText(/difficulty: 6.2\/10.0/i)).toBeInTheDocument()
    expect(screen.getByText(/spaced repetition: you have 2 reviews due/i)).toBeInTheDocument()

    // Verify recommendations
    expect(screen.getAllByText('hesitate').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/high priority/i)).toBeInTheDocument()
    expect(screen.getByText('confident')).toBeInTheDocument()

    // Verify weak words section
    expect(screen.getByText(/weak words & focus areas/i)).toBeInTheDocument()
    expect(screen.getByText('reluctant')).toBeInTheDocument()

    // Verify learning analytics
    expect(screen.getByText('65%')).toBeInTheDocument() // Avg mastery
    expect(screen.getByText('80%')).toBeInTheDocument() // Practice rate
    expect(screen.getByText('85%')).toBeInTheDocument() // Recall accuracy
  })

  it('generates a personalized scenario via interactive form', async () => {
    const user = userEvent.setup()
    vi.mocked(personalizationApi.getProfile).mockResolvedValueOnce(mockProfile)
    vi.mocked(personalizationApi.getRecommendations).mockResolvedValueOnce(mockRecommendationsResponse)
    vi.mocked(personalizationApi.generateScenario).mockResolvedValueOnce(mockGeneratedScenario)

    renderPersonalizationPage()

    await waitFor(() => {
      expect(screen.getByText(/ai personalized scenario generator/i)).toBeInTheDocument()
    })

    const wordInput = screen.getByPlaceholderText(/e.g., negotiate, hesitate/i)
    await user.type(wordInput, 'hesitate')

    const generateBtn = screen.getByRole('button', { name: /generate personalized scenario/i })
    await user.click(generateBtn)

    expect(personalizationApi.generateScenario).toHaveBeenCalledWith({
      word: 'hesitate',
      domain: 'Workplace & Business',
      weak_area_context: undefined,
    })

    await waitFor(() => {
      expect(screen.getByText(/during a quarterly team sync/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/politely convey your hesitation/i)).toBeInTheDocument()
    expect(screen.getByText(/hint: be constructive/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /practice this word now/i })).toBeInTheDocument()
  })

  it('renders error state when profile query fails and allows retry', async () => {
    vi.mocked(personalizationApi.getProfile).mockRejectedValueOnce(new Error('Network error'))
    vi.mocked(personalizationApi.getRecommendations).mockResolvedValueOnce(mockRecommendationsResponse)

    renderPersonalizationPage()

    await waitFor(() => {
      expect(screen.getByText(/could not load personalized plan/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })
})
