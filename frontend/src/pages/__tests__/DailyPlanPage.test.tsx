import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { DailyPlanPage } from '@/pages/DailyPlanPage'
import { dailyApi } from '@/api/daily'
import { DailyPlanResponse } from '@/types'

vi.mock('@/api/daily', () => ({
  dailyApi: {
    getDailyPlan: vi.fn(),
  },
}))

const mockDailyPlan: DailyPlanResponse = {
  date: '2026-09-16',
  daily_goal_target: 5,
  daily_goal_progress: 3,
  is_goal_completed: false,
  current_streak: 4,
  word_of_the_day: {
    word: 'resilient',
    meaning: 'Able to withstand or recover quickly from difficult conditions.',
    cefr_level: 'B2',
    part_of_speech: 'adjective',
    example_sentence: 'She remained resilient throughout the project.',
  },
  tasks: [
    {
      id: 'task_reviews_due',
      priority: 1,
      task_type: 'reviews_due',
      title: 'Due Spaced Reviews',
      description: 'Active recall reviews scheduled for today.',
      status: 'pending',
      item_count: 2,
      action_label: 'Start Reviews',
      action_url: '/reviews',
      items: [
        { id: '1', word: 'hesitate', status: 'practiced' },
        { id: '2', word: 'vividly', status: 'recalled' },
      ],
    },
    {
      id: 'task_struggling_practice',
      priority: 2,
      task_type: 'struggling_practice',
      title: 'Struggling Words Targeted Practice',
      description: 'Targeted scenario practice for struggling words.',
      status: 'pending',
      item_count: 1,
      action_label: 'Practice Struggling Words',
      action_url: '/practice',
      items: [{ id: '3', word: 'hassle', status: 'struggling' }],
    },
    {
      id: 'task_learn_new',
      priority: 3,
      task_type: 'learn_new',
      title: 'Learn New Vocabulary',
      description: 'Expand your active vocabulary pool.',
      status: 'pending',
      item_count: 2,
      action_label: 'Learn Words',
      action_url: '/vocabulary',
    },
    {
      id: 'task_use_my_vocabulary',
      priority: 4,
      task_type: 'use_my_vocabulary',
      title: 'Use My Vocabulary (Multi-Word Synthesis)',
      description: 'Synthesize 3 active vocabulary words.',
      status: 'ready',
      item_count: 3,
      action_label: 'Start Multi-Word Practice',
      action_url: '/practice/multi-word',
    },
  ],
  completed_tasks_count: 0,
  total_tasks_count: 4,
  completion_percentage: 0.0,
}

describe('DailyPlanPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders daily plan loading state', () => {
    vi.mocked(dailyApi.getDailyPlan).mockReturnValue(new Promise(() => {}))
    render(
      <MemoryRouter>
        <DailyPlanPage />
      </MemoryRouter>
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders error state and retries successfully', async () => {
    const user = userEvent.setup()
    vi.mocked(dailyApi.getDailyPlan).mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter>
        <DailyPlanPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Could not load Daily Plan')).toBeInTheDocument()
    })

    vi.mocked(dailyApi.getDailyPlan).mockResolvedValue(mockDailyPlan)
    const retryBtn = screen.getByRole('button', { name: /try again/i })
    await user.click(retryBtn)

    await waitFor(() => {
      expect(screen.getByText("Today's Learning Plan")).toBeInTheDocument()
    })
  })

  it('renders streak, goal progress, word of the day, and prioritized tasks', async () => {
    vi.mocked(dailyApi.getDailyPlan).mockResolvedValue(mockDailyPlan)

    render(
      <MemoryRouter>
        <DailyPlanPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText("Today's Learning Plan")).toBeInTheDocument()
    })

    // Header & Streak
    expect(screen.getByText('4 Days')).toBeInTheDocument()
    expect(screen.getByText(/3 \/ 5 Activities/)).toBeInTheDocument()

    // Word of the day
    expect(screen.getByText('resilient')).toBeInTheDocument()
    expect(screen.getByText(/Able to withstand/)).toBeInTheDocument()

    // Tasks
    expect(screen.getByText('Due Spaced Reviews')).toBeInTheDocument()
    expect(screen.getByText('Struggling Words Targeted Practice')).toBeInTheDocument()
    expect(screen.getByText('Learn New Vocabulary')).toBeInTheDocument()
    expect(screen.getByText('Use My Vocabulary (Multi-Word Synthesis)')).toBeInTheDocument()

    // Action buttons
    expect(screen.getByRole('button', { name: /Start Reviews/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Practice Struggling Words/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start Multi-Word Practice/i })).toBeInTheDocument()
  })
})
