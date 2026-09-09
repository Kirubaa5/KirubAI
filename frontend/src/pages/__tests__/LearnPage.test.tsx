import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LearnPage } from '@/pages/LearnPage'
import { vocabularyApi } from '@/api/vocabulary'
import { Vocabulary } from '@/types'

vi.mock('@/api/vocabulary', () => ({
  vocabularyApi: {
    getLearningContent: vi.fn(),
    markLearned: vi.fn(),
  },
}))

const mockVocabulary: Vocabulary = {
  id: 'vocab-123',
  word: 'hesitate',
  status: 'new',
  mastery_score: 0.0,
  practice_count: 0,
  successful_usage_count: 0,
  failed_recall_count: 0,
  review_interval_days: 1,
  created_at: '2026-03-01T00:00:00Z',
  details: {
    simple_meaning: 'To pause before saying or doing something because of uncertainty.',
    contextual_meaning: 'Used when someone shows reluctance or pauses to make a thoughtful choice.',
    part_of_speech: 'verb',
    pronunciation_text: 'HEZ-ih-tayt',
    cefr_level: 'B1',
    difficulty_score: 4.0,
    synonyms: ['pause', 'waver', 'falter'],
    antonyms: ['decide', 'commit', 'proceed'],
    word_forms: {
      verb: 'hesitate',
      noun: 'hesitation',
      adjective: 'hesitant',
      adverb: 'hesitantly',
    },
    collocations: [
      'hesitate to ask',
      "don't hesitate",
      'hesitate for a moment',
      'without hesitating',
    ],
  },
  examples: [
    {
      id: 'ex-1',
      context_label: 'Workplace',
      example_text: "Please don't hesitate to reach out if you have any questions.",
      order_index: 0,
    },
    {
      id: 'ex-2',
      context_label: 'Friends',
      example_text: 'I hesitated for a second before telling my friend the truth.',
      order_index: 1,
    },
    {
      id: 'ex-3',
      context_label: 'Meeting',
      example_text: 'The team lead hesitated before approving the final budget.',
      order_index: 2,
    },
    {
      id: 'ex-4',
      context_label: 'Interview',
      example_text: 'I hesitated briefly to gather my thoughts.',
      order_index: 3,
    },
    {
      id: 'ex-5',
      context_label: 'College',
      example_text: 'She hesitated to raise her hand in class.',
      order_index: 4,
    },
    {
      id: 'ex-6',
      context_label: 'Family',
      example_text: "My parents didn't hesitate to support my decision.",
      order_index: 5,
    },
    {
      id: 'ex-7',
      context_label: 'Shopping',
      example_text: 'I hesitated between the two laptops.',
      order_index: 6,
    },
    {
      id: 'ex-8',
      context_label: 'Travel',
      example_text: 'We hesitated at the intersection, unsure which road to take.',
      order_index: 7,
    },
    {
      id: 'ex-9',
      context_label: 'Phone call',
      example_text: 'He hesitated on the phone when I asked if he was free.',
      order_index: 8,
    },
    {
      id: 'ex-10',
      context_label: 'Daily life',
      example_text: "When an opportunity presents itself, don't hesitate.",
      order_index: 9,
    },
  ],
}

function renderLearnPage(vocabId = 'vocab-123') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/vocabulary/${vocabId}/learn`]}>
        <Routes>
          <Route path="/vocabulary/:id/learn" element={<LearnPage />} />
          <Route path="/vocabulary" element={<div>Vocabulary Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('LearnPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state while generating AI content', () => {
    vi.mocked(vocabularyApi.getLearningContent).mockImplementation(
      () => new Promise(() => {}) // never resolves to stay in loading
    )

    renderLearnPage()

    expect(screen.getByText(/generating ai learning content/i)).toBeInTheDocument()
  })

  it('renders error state when fetching content fails', async () => {
    vi.mocked(vocabularyApi.getLearningContent).mockRejectedValueOnce(
      new Error('Failed to load')
    )

    renderLearnPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load learning content/i)).toBeInTheDocument()
    })
  })

  it('renders full word explanation and lexical data correctly', async () => {
    vi.mocked(vocabularyApi.getLearningContent).mockResolvedValueOnce(mockVocabulary)

    renderLearnPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /hesitate/i })).toBeInTheDocument()
    })

    // Pronunciation and Part of Speech
    expect(screen.getByText('/HEZ-ih-tayt/')).toBeInTheDocument()
    expect(screen.getAllByText('verb').length).toBeGreaterThanOrEqual(1)

    // CEFR Level & Difficulty
    expect(screen.getByText('B1')).toBeInTheDocument()
    expect(screen.getByText('4.0 / 10')).toBeInTheDocument()

    // Meanings
    expect(
      screen.getByText(/to pause before saying or doing something because of uncertainty/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/used when someone shows reluctance or pauses to make a thoughtful choice/i)
    ).toBeInTheDocument()

    // Word forms
    expect(screen.getByText('hesitation')).toBeInTheDocument()
    expect(screen.getByText('hesitant')).toBeInTheDocument()

    // Synonyms & Antonyms
    expect(screen.getByText('waver')).toBeInTheDocument()
    expect(screen.getByText('decide')).toBeInTheDocument()

    // Collocations
    expect(screen.getByText('hesitate to ask')).toBeInTheDocument()
    expect(screen.getByText("don't hesitate")).toBeInTheDocument()

    // 10 Conversational Examples
    expect(screen.getByText('10 Real-Life Conversational Examples')).toBeInTheDocument()
    expect(screen.getByText('Workplace')).toBeInTheDocument()
    expect(screen.getByText('Interview')).toBeInTheDocument()
    expect(
      screen.getByText(/"Please don't hesitate to reach out if you have any questions."/i)
    ).toBeInTheDocument()
  })

  it('allows user to mark word as learned', async () => {
    const user = userEvent.setup()
    vi.mocked(vocabularyApi.getLearningContent).mockResolvedValueOnce(mockVocabulary)
    vi.mocked(vocabularyApi.markLearned).mockResolvedValueOnce({
      ...mockVocabulary,
      status: 'learned',
      mastery_score: 0.15,
    })

    renderLearnPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /mark as understood/i })).toBeInTheDocument()
    })

    const markButton = screen.getByRole('button', { name: /mark as understood/i })
    await user.click(markButton)

    expect(vocabularyApi.markLearned).toHaveBeenCalledWith('vocab-123')
  })

  it('displays learned status when word is already learned', async () => {
    vi.mocked(vocabularyApi.getLearningContent).mockResolvedValueOnce({
      ...mockVocabulary,
      status: 'learned',
      mastery_score: 0.15,
    })

    renderLearnPage()

    await waitFor(() => {
      expect(screen.getByText('Status: Learned')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /return to vocabulary list/i })).toBeInTheDocument()
  })
})
