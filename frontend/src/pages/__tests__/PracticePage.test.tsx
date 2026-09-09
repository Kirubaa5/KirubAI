import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PracticePage } from '@/pages/PracticePage'
import { practiceApi } from '@/api/practice'
import { vocabularyApi } from '@/api/vocabulary'
import { PracticeStartResponse, PracticeSubmitResponse, Scenario, Vocabulary } from '@/types'

vi.mock('@/api/practice', () => ({
  practiceApi: {
    start: vi.fn(),
    getScenario: vi.fn(),
    submit: vi.fn(),
    getSession: vi.fn(),
    listSessions: vi.fn(),
    complete: vi.fn(),
  },
}))

vi.mock('@/api/vocabulary', () => ({
  vocabularyApi: {
    get: vi.fn(),
  },
}))

const mockVocabulary: Vocabulary = {
  id: 'vocab-123',
  word: 'hesitate',
  status: 'learned',
  mastery_score: 0.2,
  practice_count: 1,
  successful_usage_count: 1,
  failed_recall_count: 0,
  review_interval_days: 1,
  created_at: '2026-03-01T00:00:00Z',
  details: {
    simple_meaning: 'To pause before doing something because of uncertainty.',
    pronunciation_text: 'HEZ-ih-tayt',
    cefr_level: 'B1',
    synonyms: ['pause'],
    antonyms: ['decide'],
    word_forms: { verb: 'hesitate' },
    collocations: ["don't hesitate"],
  },
}

const mockStartResponse: PracticeStartResponse = {
  session_id: 'session-456',
  vocabulary_id: 'vocab-123',
  target_word: 'hesitate',
  scenario: {
    situation: 'Your manager asks whether you can take on an urgent feature deadline for Friday.',
    prompt: 'Respond politely expressing your hesitation using the target word "hesitate".',
    context_hint: 'Be respectful and explain your workload while offering to discuss priorities.',
  },
}

const mockSubmitResponse: PracticeSubmitResponse = {
  attempt_id: 'attempt-789',
  session_id: 'session-456',
  vocabulary_id: 'vocab-123',
  target_word: 'hesitate',
  scenario_text: 'Your manager asks whether you can take on an urgent feature deadline for Friday.',
  user_response: 'I would hesitate to take this on because my backlog is full.',
  scores: {
    vocabulary_usage: 9.0,
    grammar: 8.5,
    context: 9.0,
    naturalness: 8.5,
    overall: 8.7,
  },
  feedback: 'Excellent usage of the target word! Your phrasing is natural and fits the scenario perfectly.',
  improved_version: 'I hesitate to commit right now because my schedule is already booked.',
  is_successful: true,
  can_continue: true,
}

function renderPracticePage(vocabId = 'vocab-123') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/practice/${vocabId}`]}>
        <Routes>
          <Route path="/practice/:id" element={<PracticePage />} />
          <Route path="/vocabulary" element={<div>Vocabulary Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PracticePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(vocabularyApi.get).mockResolvedValue(mockVocabulary)
  })

  it('renders loading state while preparing practice session', () => {
    vi.mocked(practiceApi.start).mockImplementation(
      () => new Promise(() => {}) // pending promise
    )

    renderPracticePage()

    expect(screen.getByText(/preparing practice session/i)).toBeInTheDocument()
  })

  it('renders error state when starting session fails', async () => {
    vi.mocked(practiceApi.start).mockRejectedValueOnce(new Error('Network error'))

    renderPracticePage()

    await waitFor(() => {
      expect(screen.getByText(/failed to start practice session/i)).toBeInTheDocument()
    })
  })

  it('renders scenario situation, prompt, hint, and target word', async () => {
    vi.mocked(practiceApi.start).mockResolvedValueOnce(mockStartResponse)

    renderPracticePage()

    await waitFor(() => {
      expect(screen.getByText(mockStartResponse.scenario.situation)).toBeInTheDocument()
    })

    expect(screen.getByText(mockStartResponse.scenario.prompt)).toBeInTheDocument()
    expect(screen.getByText(mockStartResponse.scenario.context_hint!)).toBeInTheDocument()
    expect(screen.getAllByText(/hesitate/i).length).toBeGreaterThanOrEqual(1)
  })

  it('allows user to type response and submit for AI evaluation', async () => {
    const user = userEvent.setup()
    vi.mocked(practiceApi.start).mockResolvedValueOnce(mockStartResponse)
    vi.mocked(practiceApi.submit).mockResolvedValueOnce(mockSubmitResponse)

    renderPracticePage()

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'I would hesitate to take this on because my backlog is full.')

    const submitBtn = screen.getByRole('button', { name: /submit & evaluate/i })
    await user.click(submitBtn)

    expect(practiceApi.submit).toHaveBeenCalledWith(
      'session-456',
      mockStartResponse.scenario.situation,
      'I would hesitate to take this on because my backlog is full.'
    )

    // Check evaluation result is displayed
    await waitFor(() => {
      expect(screen.getByText(/great attempt! word practiced successfully/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/8.7/i)).toBeInTheDocument()
    expect(screen.getAllByText(/9.0\/10/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(mockSubmitResponse.feedback)).toBeInTheDocument()
    expect(
      screen.getByText(`"${mockSubmitResponse.improved_version}"`)
    ).toBeInTheDocument()
  })

  it('allows retrying the current scenario', async () => {
    const user = userEvent.setup()
    vi.mocked(practiceApi.start).mockResolvedValueOnce(mockStartResponse)
    vi.mocked(practiceApi.submit).mockResolvedValueOnce(mockSubmitResponse)

    renderPracticePage()

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    await user.type(screen.getByRole('textbox'), 'I would hesitate.')
    await user.click(screen.getByRole('button', { name: /submit & evaluate/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry this scenario/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /retry this scenario/i }))

    // Back to input mode
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('allows requesting a new scenario in the session', async () => {
    const user = userEvent.setup()
    const newScenario: Scenario = {
      situation: 'Your friend invites you to an impromptu weekend road trip.',
      prompt: 'Politely express your hesitation due to prior commitments.',
      context_hint: 'Use a casual, friendly tone.',
    }

    vi.mocked(practiceApi.start).mockResolvedValueOnce(mockStartResponse)
    vi.mocked(practiceApi.getScenario).mockResolvedValueOnce(newScenario)

    renderPracticePage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new scenario/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /new scenario/i }))

    expect(practiceApi.getScenario).toHaveBeenCalledWith('session-456')

    await waitFor(() => {
      expect(screen.getByText(newScenario.situation)).toBeInTheDocument()
    })
  })
})
