import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AchievementsPage } from '@/pages/AchievementsPage'
import { gamificationApi } from '@/api/gamification'
import {
  GamificationOverview,
  AchievementListResponse,
  LevelRoadmapResponse,
} from '@/types'

vi.mock('@/api/gamification', () => ({
  gamificationApi: {
    getOverview: vi.fn(),
    getAchievements: vi.fn(),
    getLevels: vi.fn(),
  },
}))

const mockOverview: GamificationOverview = {
  level: 3,
  level_title: 'Word Builder',
  total_xp: 240,
  current_level_xp: 200,
  next_level_xp: 300,
  xp_within_level: 40,
  xp_required_for_next_level: 100,
  level_progress_percentage: 40.0,
  current_streak: 5,
  longest_streak: 7,
  daily_goal: 5,
  daily_goal_progress: 3,
  is_daily_goal_completed: false,
  unlocked_achievements_count: 3,
  total_achievements_count: 16,
  achievement_completion_percentage: 18.8,
  recent_achievements: [
    {
      key: 'first_word',
      title: 'First Word',
      description: 'Add and learn your first vocabulary word',
      category: 'vocabulary',
      icon: 'BookOpen',
      target_threshold: 1,
      current_progress: 1,
      progress_percentage: 100.0,
      is_unlocked: true,
      achieved_at: '2026-09-10T12:00:00Z',
    },
  ],
  next_achievements: [
    {
      key: 'word_collector',
      title: 'Word Collector',
      description: 'Build your vocabulary with 10 words',
      category: 'vocabulary',
      icon: 'Bookmark',
      target_threshold: 10,
      current_progress: 6,
      progress_percentage: 60.0,
      is_unlocked: false,
    },
  ],
}

const mockAchievementsResponse: AchievementListResponse = {
  total: 4,
  unlocked_count: 2,
  completion_percentage: 50.0,
  items: [
    {
      key: 'first_word',
      title: 'First Word',
      description: 'Add and learn your first vocabulary word',
      category: 'vocabulary',
      icon: 'BookOpen',
      target_threshold: 1,
      current_progress: 1,
      progress_percentage: 100.0,
      is_unlocked: true,
      achieved_at: '2026-09-10T12:00:00Z',
    },
    {
      key: 'word_collector',
      title: 'Word Collector',
      description: 'Build your vocabulary with 10 words',
      category: 'vocabulary',
      icon: 'Bookmark',
      target_threshold: 10,
      current_progress: 6,
      progress_percentage: 60.0,
      is_unlocked: false,
    },
    {
      key: 'first_step',
      title: 'First Step',
      description: 'Complete your first scenario practice attempt',
      category: 'practice',
      icon: 'Target',
      target_threshold: 1,
      current_progress: 1,
      progress_percentage: 100.0,
      is_unlocked: true,
      achieved_at: '2026-09-12T15:30:00Z',
    },
    {
      key: 'scenario_pro',
      title: 'Scenario Pro',
      description: 'Complete 10 scenario practice attempts',
      category: 'practice',
      icon: 'Zap',
      target_threshold: 10,
      current_progress: 3,
      progress_percentage: 30.0,
      is_unlocked: false,
    },
  ],
}

const mockLevelsResponse: LevelRoadmapResponse = {
  current_level: 3,
  current_xp: 240,
  level_title: 'Word Builder',
  current_level_xp: 200,
  next_level_xp: 300,
  xp_within_level: 40,
  progress_percentage: 40.0,
  levels: [
    {
      level: 1,
      title: 'Novice Explorer',
      xp_required: 0,
      is_unlocked: true,
      is_current: false,
    },
    {
      level: 2,
      title: 'Curious Learner',
      xp_required: 100,
      is_unlocked: true,
      is_current: false,
    },
    {
      level: 3,
      title: 'Word Builder',
      xp_required: 200,
      is_unlocked: true,
      is_current: true,
    },
    {
      level: 4,
      title: 'Vocabulary Apprentice',
      xp_required: 300,
      is_unlocked: false,
      is_current: false,
    },
  ],
}

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AchievementsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(gamificationApi.getOverview).mockReturnValue(new Promise(() => {}))
    vi.mocked(gamificationApi.getAchievements).mockReturnValue(new Promise(() => {}))
    vi.mocked(gamificationApi.getLevels).mockReturnValue(new Promise(() => {}))

    renderWithClient(<AchievementsPage />)

    expect(screen.getByText(/loading achievements/i)).toBeInTheDocument()
  })

  it('renders error state and handles retry', async () => {
    const user = userEvent.setup()
    vi.mocked(gamificationApi.getOverview).mockRejectedValueOnce(new Error('Network error'))
    vi.mocked(gamificationApi.getAchievements).mockRejectedValueOnce(new Error('Network error'))

    renderWithClient(<AchievementsPage />)

    await waitFor(() => {
      expect(screen.getByText('Could not load achievements')).toBeInTheDocument()
    })

    // Setup success on retry
    vi.mocked(gamificationApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievementsResponse)
    vi.mocked(gamificationApi.getLevels).mockResolvedValue(mockLevelsResponse)

    const retryBtn = screen.getByRole('button', { name: /try again/i })
    await user.click(retryBtn)

    await waitFor(() => {
      expect(screen.getByText('Gamification & Achievements')).toBeInTheDocument()
    })
  })

  it('renders level info, XP progress, streaks, and daily goal', async () => {
    vi.mocked(gamificationApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievementsResponse)
    vi.mocked(gamificationApi.getLevels).mockResolvedValue(mockLevelsResponse)

    renderWithClient(<AchievementsPage />)

    await waitFor(() => {
      expect(screen.getByText('Word Builder')).toBeInTheDocument()
    })

    expect(screen.getByText(/240 XP/)).toBeInTheDocument()
    expect(screen.getByText(/40 \/ 100 XP/)).toBeInTheDocument()
    expect(screen.getByText(/60 XP needed for Level 4/)).toBeInTheDocument()
    expect(screen.getByText(/5 days/)).toBeInTheDocument()
    expect(screen.getByText(/Best: 7/)).toBeInTheDocument()
    expect(screen.getByText(/3 \/ 5/)).toBeInTheDocument()
  })

  it('renders unlocked and locked achievements correctly', async () => {
    vi.mocked(gamificationApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievementsResponse)
    vi.mocked(gamificationApi.getLevels).mockResolvedValue(mockLevelsResponse)

    renderWithClient(<AchievementsPage />)

    await waitFor(() => {
      expect(screen.getByText('First Word')).toBeInTheDocument()
      expect(screen.getByText('Word Collector')).toBeInTheDocument()
      expect(screen.getByText('First Step')).toBeInTheDocument()
      expect(screen.getByText('Scenario Pro')).toBeInTheDocument()
    })

    // Check unlocked status and dates
    expect(screen.getByText('Sep 10, 2026')).toBeInTheDocument()

    // Check locked progress
    expect(screen.getByText('6 / 10')).toBeInTheDocument()
    expect(screen.getByText('3 / 10')).toBeInTheDocument()
  })

  it('filters achievements by category tabs', async () => {
    const user = userEvent.setup()
    vi.mocked(gamificationApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievementsResponse)
    vi.mocked(gamificationApi.getLevels).mockResolvedValue(mockLevelsResponse)

    renderWithClient(<AchievementsPage />)

    await waitFor(() => {
      expect(screen.getByText('First Word')).toBeInTheDocument()
      expect(screen.getByText('First Step')).toBeInTheDocument()
    })

    // Click "Vocabulary" category
    const vocabBtn = screen.getByRole('button', { name: /vocabulary/i })
    await user.click(vocabBtn)

    expect(screen.getByText('First Word')).toBeInTheDocument()
    expect(screen.getByText('Word Collector')).toBeInTheDocument()
    expect(screen.queryByText('First Step')).not.toBeInTheDocument()
    expect(screen.queryByText('Scenario Pro')).not.toBeInTheDocument()

    // Click "Practice" category
    const practiceBtn = screen.getByRole('button', { name: /practice/i })
    await user.click(practiceBtn)

    expect(screen.queryByText('First Word')).not.toBeInTheDocument()
    expect(screen.getByText('First Step')).toBeInTheDocument()
    expect(screen.getByText('Scenario Pro')).toBeInTheDocument()
  })

  it('toggles level roadmap drawer to inspect all levels', async () => {
    const user = userEvent.setup()
    vi.mocked(gamificationApi.getOverview).mockResolvedValue(mockOverview)
    vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievementsResponse)
    vi.mocked(gamificationApi.getLevels).mockResolvedValue(mockLevelsResponse)

    renderWithClient(<AchievementsPage />)

    await waitFor(() => {
      expect(screen.getByText('Level Roadmap & Milestones')).toBeInTheDocument()
    })

    expect(screen.queryByText('Vocabulary Apprentice')).not.toBeInTheDocument()

    // Click to expand roadmap
    const roadmapToggle = screen.getByText('Level Roadmap & Milestones')
    await user.click(roadmapToggle)

    expect(screen.getByText('Novice Explorer')).toBeInTheDocument()
    expect(screen.getByText('Curious Learner')).toBeInTheDocument()
    expect(screen.getByText('Vocabulary Apprentice')).toBeInTheDocument()
  })
})
