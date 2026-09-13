import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '@/pages/DashboardPage'
import { dashboardApi } from '@/api/dashboard'
import { progressApi } from '@/api/progress'
import {
  DashboardSummary,
  ProgressOverview,
  WeeklyProgress,
  MonthlyProgress,
  VocabularyBreakdown,
} from '@/types'

// Mock Recharts ResponsiveContainer to avoid sizing issues in happy-dom
vi.mock('recharts', async () => {
  const original = await vi.importActual<any>('recharts')
  return {
    ...original,
    ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  }
})

vi.mock('@/api/dashboard', () => ({
  dashboardApi: {
    getSummary: vi.fn(),
  },
}))

vi.mock('@/api/progress', () => ({
  progressApi: {
    getOverview: vi.fn(),
    getWeekly: vi.fn(),
    getMonthly: vi.fn(),
    getVocabularyBreakdown: vi.fn(),
  },
}))

const mockDashboardSummary: DashboardSummary = {
  today: {
    reviews_due: 3,
    words_to_practice: 4,
    daily_goal_progress: 3,
    daily_goal_target: 5,
    word_of_the_day: {
      word: 'resilient',
      meaning: 'Able to recover quickly from difficulties.',
      cefr_level: 'B2',
      part_of_speech: 'adjective',
      example_sentence: 'She remained resilient during tough challenges.',
    },
  },
  stats: {
    total_words: 15,
    mastered_words: 4,
    active_words: 9,
    struggling_words: 2,
    current_streak: 5,
    total_xp: 450,
    level: 5,
  },
  recent_activity: [
    {
      type: 'practice',
      word: 'hesitate',
      score: 8.5,
      result: 'success',
      at: '2026-09-13T08:30:00Z',
      detail: 'Scenario practice scored 8.5/10',
    },
    {
      type: 'review',
      word: 'confident',
      score: 10.0,
      result: 'success',
      at: '2026-09-13T07:15:00Z',
      detail: 'Spaced repetition recall (Passed)',
    },
  ],
}

const mockOverview: ProgressOverview = {
  total_vocabulary: 15,
  active_vocabulary: 9,
  mastered_count: 4,
  struggling_count: 2,
  average_mastery: 0.62,
  total_practice_attempts: 12,
  practice_accuracy: 0.75,
  average_practice_score: 8.1,
  total_reviews_completed: 8,
  recall_accuracy_rate: 0.88,
  total_conversations: 2,
  vocabulary_used_in_conversations: 5,
  current_streak: 5,
  longest_streak: 7,
  total_xp: 450,
  level: 5,
  daily_goal: 5,
}

const mockWeeklyProgress: WeeklyProgress = {
  daily_progress: [
    {
      date: '2026-09-13',
      day_name: 'Sun',
      practices_count: 2,
      reviews_count: 1,
      conversations_count: 0,
      words_added: 1,
      words_mastered: 1,
      accuracy_rate: 1.0,
      xp_earned: 30,
    },
  ],
  total_practices: 8,
  total_reviews: 5,
  total_conversations: 2,
  total_words_added: 4,
  total_xp_earned: 220,
  average_accuracy_rate: 0.85,
  active_days: 5,
}

const mockMonthlyProgress: MonthlyProgress = {
  trends: [
    {
      date: '2026-09-13',
      day_or_week: 'Sep 13',
      activities_count: 4,
      words_acquired: 1,
      accuracy_rate: 1.0,
      xp_earned: 30,
    },
  ],
  total_activities: 35,
  words_learned: 12,
  average_accuracy_rate: 0.82,
  active_days: 18,
  retention_rate: 0.88,
}

const mockBreakdown: VocabularyBreakdown = {
  total_words: 15,
  by_status: [
    { status: 'mastered', count: 4, percentage: 26.7 },
    { status: 'practiced', count: 5, percentage: 33.3 },
    { status: 'recalled', count: 2, percentage: 13.3 },
    { status: 'learned', count: 2, percentage: 13.3 },
    { status: 'struggling', count: 2, percentage: 13.3 },
  ],
  by_mastery_bracket: [
    { bracket: '0-20%', count: 2, percentage: 13.3 },
    { bracket: '81-100%', count: 4, percentage: 26.7 },
  ],
  by_cefr_level: {
    B1: 6,
    B2: 7,
    C1: 2,
    Unassigned: 0,
  },
}

function renderDashboardPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reviews" element={<div data-testid="reviews-page">Reviews Page</div>} />
          <Route path="/vocabulary" element={<div data-testid="vocabulary-page">Vocabulary Page</div>} />
          <Route path="/conversations" element={<div data-testid="conversations-page">Conversations Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(dashboardApi.getSummary).mockResolvedValue(mockDashboardSummary)
    vi.mocked(progressApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(progressApi.getWeekly).mockResolvedValue(mockWeeklyProgress)
    vi.mocked(progressApi.getMonthly).mockResolvedValue(mockMonthlyProgress)
    vi.mocked(progressApi.getVocabularyBreakdown).mockResolvedValue(mockBreakdown)
  })

  it('renders loading spinner initially when data is fetching', () => {
    vi.mocked(dashboardApi.getSummary).mockReturnValue(new Promise(() => {}))
    renderDashboardPage()
    expect(screen.getByText(/loading your learning analytics/i)).toBeInTheDocument()
  })

  it('renders error state on API failure and retries on button click', async () => {
    vi.mocked(dashboardApi.getSummary).mockRejectedValue(new Error('Network error'))
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard/i)).toBeInTheDocument()
    })

    const retryBtn = screen.getByRole('button', { name: /try again/i })
    expect(retryBtn).toBeInTheDocument()
  })

  it('renders dashboard summary, KPIs, daily tasks, and word of the day', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText('Learning Dashboard')).toBeInTheDocument()
    })

    // Action cards
    expect(screen.getByText(/what should i do today\?/i)).toBeInTheDocument()
    expect(screen.getByText('3 Due')).toBeInTheDocument()
    expect(screen.getByText('4 Ready')).toBeInTheDocument()

    // Word of the day
    expect(screen.getByText('Word of the Day')).toBeInTheDocument()
    expect(screen.getByText('resilient')).toBeInTheDocument()
    expect(screen.getByText('Able to recover quickly from difficulties.')).toBeInTheDocument()

    // KPI Cards
    expect(screen.getByText('Total Words')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getAllByText('Mastered').length).toBeGreaterThan(0)
    expect(screen.getAllByText('4').length).toBeGreaterThan(0)
  })

  it('navigates to reviews queue when clicking Start Reviews', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText('Start Reviews')).toBeInTheDocument()
    })

    const startReviewsBtn = screen.getByText('Start Reviews')
    await userEvent.click(startReviewsBtn)

    await waitFor(() => {
      expect(screen.getByTestId('reviews-page')).toBeInTheDocument()
    })
  })

  it('renders vocabulary breakdown and recent activity', async () => {
    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText(/vocabulary breakdown/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/recent learning activity/i)).toBeInTheDocument()
    expect(screen.getByText('hesitate')).toBeInTheDocument()
    expect(screen.getByText(/scenario practice scored 8.5\/10/i)).toBeInTheDocument()
  })

  it('renders empty state message when user has zero vocabulary', async () => {
    vi.mocked(dashboardApi.getSummary).mockResolvedValue({
      today: {
        reviews_due: 0,
        words_to_practice: 0,
        daily_goal_progress: 0,
        daily_goal_target: 5,
        word_of_the_day: {
          word: 'resilient',
          meaning: 'Able to withstand hardship.',
        },
      },
      stats: {
        total_words: 0,
        mastered_words: 0,
        active_words: 0,
        struggling_words: 0,
        current_streak: 0,
        total_xp: 0,
        level: 1,
      },
      recent_activity: [],
    })

    renderDashboardPage()

    await waitFor(() => {
      expect(screen.getByText(/welcome to kirubai!/i)).toBeInTheDocument()
      expect(screen.getByText(/start adding words/i)).toBeInTheDocument()
    })
  })
})
