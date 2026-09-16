import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { MultiWordPracticePage } from '@/pages/MultiWordPracticePage'
import { practiceApi } from '@/api/practice'
import {
  MultiWordEligibleResponse,
  MultiWordStartResponse,
  MultiWordAttemptResponse,
} from '@/types'

vi.mock('@/api/practice', () => ({
  practiceApi: {
    getMultiWordEligible: vi.fn(),
    startMultiWord: vi.fn(),
    submitMultiWord: vi.fn(),
  },
}))

const mockEligibleSuccess: MultiWordEligibleResponse = {
  eligible_count: 3,
  total_words: 5,
  min_required: 3,
  is_eligible: true,
  items: [
    { id: '1', word: 'hesitate', cefr_level: 'B1', status: 'practiced' },
    { id: '2', word: 'vividly', cefr_level: 'B2', status: 'recalled' },
    { id: '3', word: 'hassle', cefr_level: 'B2', status: 'reinforced' },
  ],
}

const mockEligibleInsufficient: MultiWordEligibleResponse = {
  eligible_count: 1,
  total_words: 2,
  min_required: 3,
  is_eligible: false,
  items: [
    { id: '1', word: 'hesitate', cefr_level: 'B1', status: 'practiced' },
  ],
}

const mockStartResponse: MultiWordStartResponse = {
  session_id: 'sess-123',
  target_words: [
    { id: '1', word: 'hesitate', cefr_level: 'B1', status: 'practiced' },
    { id: '2', word: 'vividly', cefr_level: 'B2', status: 'recalled' },
    { id: '3', word: 'hassle', cefr_level: 'B2', status: 'reinforced' },
  ],
  scenario: {
    situation: 'Your team is deciding on whether to accept a tight deadline project.',
    prompt: 'Write a response addressing the team incorporating hesitate, vividly, and hassle.',
    context_hint: 'Maintain a professional and proactive tone.',
  },
  created_at: '2026-09-16T12:00:00Z',
}

const mockSubmitResponse: MultiWordAttemptResponse = {
  id: 'att-123',
  session_id: 'sess-123',
  user_response: 'Do not hesitate, remember vividly, avoid hassle.',
  scores: {
    vocabulary_usage: 9.0,
    grammar: 8.5,
    context: 9.0,
    naturalness: 8.5,
    overall: 8.8,
  },
  word_evaluations: [
    {
      word: 'hesitate',
      used: true,
      used_correctly: true,
      used_naturally: true,
      score: 9.0,
      feedback: "Great use of 'hesitate'.",
    },
    {
      word: 'vividly',
      used: true,
      used_correctly: true,
      used_naturally: true,
      score: 9.0,
      feedback: "Natural use of 'vividly'.",
    },
    {
      word: 'hassle',
      used: true,
      used_correctly: true,
      used_naturally: true,
      score: 9.0,
      feedback: "Accurate context for 'hassle'.",
    },
  ],
  feedback: 'Outstanding synthesis of all target vocabulary words!',
  improved_version: 'We should not hesitate; keeping our goals vividly in mind minimizes team hassle.',
  is_successful: true,
  xp_earned: 20,
  created_at: '2026-09-16T12:05:00Z',
}

describe('MultiWordPracticePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(practiceApi.getMultiWordEligible).mockReturnValue(new Promise(() => {}))
    render(
      <MemoryRouter>
        <MultiWordPracticePage />
      </MemoryRouter>
    )
    expect(screen.getByText(/Generating realistic multi-word practice scenario/i)).toBeInTheDocument()
  })

  it('renders unlock guidance when user has fewer than 3 eligible words', async () => {
    vi.mocked(practiceApi.getMultiWordEligible).mockResolvedValue(mockEligibleInsufficient)

    render(
      <MemoryRouter>
        <MultiWordPracticePage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Unlock "Use My Vocabulary"')).toBeInTheDocument()
    })

    expect(screen.getByText(/1 of 3/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Practice Single Words/i })).toBeInTheDocument()
  })

  it('renders multi-word practice session with target words and scenario', async () => {
    vi.mocked(practiceApi.getMultiWordEligible).mockResolvedValue(mockEligibleSuccess)
    vi.mocked(practiceApi.startMultiWord).mockResolvedValue(mockStartResponse)

    render(
      <MemoryRouter>
        <MultiWordPracticePage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Multi-Word Contextual Challenge')).toBeInTheDocument()
    })

    // Target words chips
    expect(screen.getByText('hesitate')).toBeInTheDocument()
    expect(screen.getByText('vividly')).toBeInTheDocument()
    expect(screen.getByText('hassle')).toBeInTheDocument()

    // Scenario
    expect(screen.getByText(/Your team is deciding on whether to accept/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Type your response here using all target vocabulary words/)).toBeInTheDocument()
  })

  it('submits response and displays comprehensive evaluation results', async () => {
    const user = userEvent.setup()
    vi.mocked(practiceApi.getMultiWordEligible).mockResolvedValue(mockEligibleSuccess)
    vi.mocked(practiceApi.startMultiWord).mockResolvedValue(mockStartResponse)
    vi.mocked(practiceApi.submitMultiWord).mockResolvedValue(mockSubmitResponse)

    render(
      <MemoryRouter>
        <MultiWordPracticePage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Type your response here/)).toBeInTheDocument()
    })

    const textarea = screen.getByPlaceholderText(/Type your response here/)
    await user.type(textarea, 'Do not hesitate, remember vividly, avoid hassle.')

    const submitBtn = screen.getByRole('button', { name: /Submit & Evaluate/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Synthesis Success!')).toBeInTheDocument()
    })

    expect(screen.getByText('8.8')).toBeInTheDocument()
    expect(screen.getByText(/Outstanding synthesis of all target vocabulary words/)).toBeInTheDocument()
    expect(screen.getByText("Great use of 'hesitate'.")).toBeInTheDocument()
    expect(screen.getByText("Natural use of 'vividly'.")).toBeInTheDocument()
    expect(screen.getByText("Accurate context for 'hassle'.")).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Next Scenario/i })).toBeInTheDocument()
  })
})
