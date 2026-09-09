import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReviewsPage } from '@/pages/ReviewsPage'
import { reviewsApi } from '@/api/reviews'
import { DueReviewsResponse, ReviewSubmitResponse } from '@/types'

vi.mock('@/api/reviews', () => ({
  reviewsApi: {
    getDue: vi.fn(),
    submit: vi.fn(),
    getHistory: vi.fn(),
  },
}))

const mockDueResponse: DueReviewsResponse = {
  due_count: 2,
  items: [
    {
      vocabulary_id: 'vocab-1',
      word: 'hesitate',
      status: 'practiced',
      mastery_score: 0.35,
      review_interval_days: 1,
      review_type: 'recall',
      prompt: {
        prompt_type: 'recall',
        definition: 'To pause before doing something because you are uncertain.',
        part_of_speech: 'verb',
        cloze_sentence: 'I _____ before answering the tough question.',
        hint: "Starts with 'H' (8 letters)",
        context_label: 'Interview',
        synonyms_hint: ['pause', 'waver'],
      },
    },
    {
      vocabulary_id: 'vocab-2',
      word: 'diligent',
      status: 'recalled',
      mastery_score: 0.6,
      review_interval_days: 3,
      review_type: 'recall',
      prompt: {
        prompt_type: 'recall',
        definition: 'Showing steady and earnest care in energetic work.',
        part_of_speech: 'adjective',
        cloze_sentence: 'She is a _____ worker who always finishes ahead of schedule.',
        hint: "Starts with 'D' (8 letters)",
        context_label: 'Workplace',
        synonyms_hint: ['hardworking', 'assiduous'],
      },
    },
  ],
}

const mockSubmitSuccess: ReviewSubmitResponse = {
  recall_successful: true,
  score: 10.0,
  feedback: "Excellent! You recalled 'hesitate' perfectly.",
  previous_status: 'practiced',
  new_status: 'recalled',
  previous_interval_days: 1,
  new_interval_days: 3,
  next_review_at: '2026-03-12T00:00:00Z',
  mastery_score: 0.45,
  xp_earned: 10,
  target_word: 'hesitate',
}

const mockSubmitFailure: ReviewSubmitResponse = {
  recall_successful: false,
  score: 3.0,
  feedback: "The correct target word was 'hesitate'. Keep practicing to strengthen your recall!",
  previous_status: 'practiced',
  new_status: 'practiced',
  previous_interval_days: 1,
  new_interval_days: 1,
  next_review_at: '2026-03-10T00:00:00Z',
  mastery_score: 0.3,
  xp_earned: 3,
  target_word: 'hesitate',
}

function renderReviewsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/reviews']}>
        <Routes>
          <Route path="/reviews" element={<ReviewsPage />} />
          <Route path="/vocabulary" element={<div>Vocabulary Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ReviewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state while fetching queue', () => {
    vi.mocked(reviewsApi.getDue).mockImplementation(
      () => new Promise(() => {}) // pending
    )

    renderReviewsPage()

    expect(screen.getByText(/loading review queue/i)).toBeInTheDocument()
  })

  it('renders error state when fetching reviews fails', async () => {
    vi.mocked(reviewsApi.getDue).mockRejectedValueOnce(new Error('Network error'))

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load review queue/i)).toBeInTheDocument()
    })
  })

  it('renders empty state when no reviews are due', async () => {
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce({
      due_count: 0,
      items: [],
    })

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByText(/you're all caught up!/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/no vocabulary words are due/i)).toBeInTheDocument()
  })

  it('renders active recall prompt card with definition and cloze sentence', async () => {
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce(mockDueResponse)

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByText(/word 1 of 2/i)).toBeInTheDocument()
    })

    expect(
      screen.getByText(`"${mockDueResponse.items[0].prompt.definition}"`)
    ).toBeInTheDocument()
    expect(
      screen.getByText(`"${mockDueResponse.items[0].prompt.cloze_sentence}"`)
    ).toBeInTheDocument()
    expect(screen.getByText('verb')).toBeInTheDocument()
    expect(screen.getByText('Interview')).toBeInTheDocument()

    // Does not show hint by default
    expect(screen.queryByText(/starts with 'h'/i)).not.toBeInTheDocument()
  })

  it('reveals memory hint when hint button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce(mockDueResponse)

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByText(/need a hint\?/i)).toBeInTheDocument()
    })

    await user.click(screen.getByText(/need a hint\?/i))

    expect(screen.getByText(/starts with 'h' \(8 letters\)/i)).toBeInTheDocument()
    expect(screen.getByText(/pause, waver/i)).toBeInTheDocument()
  })

  it('allows user to submit correct answer and displays success evaluation feedback', async () => {
    const user = userEvent.setup()
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce(mockDueResponse)
    vi.mocked(reviewsApi.submit).mockResolvedValueOnce(mockSubmitSuccess)

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    const input = screen.getByRole('textbox')
    await user.type(input, 'hesitate')

    const submitBtn = screen.getByRole('button', { name: /submit answer/i })
    await user.click(submitBtn)

    expect(reviewsApi.submit).toHaveBeenCalledWith('vocab-1', 'hesitate', 'recall')

    await waitFor(() => {
      expect(screen.getByText(/recalled successfully!/i)).toBeInTheDocument()
    })

    expect(screen.getByText(mockSubmitSuccess.feedback)).toBeInTheDocument()
    expect(screen.getByText('+10 XP')).toBeInTheDocument()
    expect(screen.getByText('10.0/10')).toBeInTheDocument()
    expect(screen.getByText(/3 days/i)).toBeInTheDocument()
    expect(screen.getByText(/45%/i)).toBeInTheDocument()
    expect(screen.getByText('recalled')).toBeInTheDocument()
  })

  it('allows user to submit incorrect answer and displays failure feedback', async () => {
    const user = userEvent.setup()
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce(mockDueResponse)
    vi.mocked(reviewsApi.submit).mockResolvedValueOnce(mockSubmitFailure)

    renderReviewsPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    await user.type(screen.getByRole('textbox'), 'wrongword')
    await user.click(screen.getByRole('button', { name: /submit answer/i }))

    await waitFor(() => {
      expect(screen.getByText(/needs review/i)).toBeInTheDocument()
    })

    expect(screen.getByText(mockSubmitFailure.feedback)).toBeInTheDocument()
    expect(screen.getByText('+3 XP')).toBeInTheDocument()
    expect(screen.getByText('3.0/10')).toBeInTheDocument()
  })

  it('advances through the queue and shows completion card on finish', async () => {
    const user = userEvent.setup()
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce(mockDueResponse)
    vi.mocked(reviewsApi.submit)
      .mockResolvedValueOnce(mockSubmitSuccess)
      .mockResolvedValueOnce({
        ...mockSubmitSuccess,
        target_word: 'diligent',
        previous_status: 'recalled',
        new_status: 'reinforced',
        new_interval_days: 7,
      })

    renderReviewsPage()

    // 1st word submission
    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })
    await user.type(screen.getByRole('textbox'), 'hesitate')
    await user.click(screen.getByRole('button', { name: /submit answer/i }))

    // Click Next Word in Queue
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /next word in queue/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /next word in queue/i }))

    // 2nd word prompt displayed
    await waitFor(() => {
      expect(screen.getByText(/word 2 of 2/i)).toBeInTheDocument()
    })
    expect(
      screen.getByText(`"${mockDueResponse.items[1].prompt.definition}"`)
    ).toBeInTheDocument()

    // 2nd word submission
    await user.type(screen.getByRole('textbox'), 'diligent')
    await user.click(screen.getByRole('button', { name: /submit answer/i }))

    // Click Finish Session
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /finish session/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /finish session/i }))

    // Completion summary view
    await waitFor(() => {
      expect(screen.getByText(/review session complete!/i)).toBeInTheDocument()
    })
    expect(screen.getAllByText('2').length).toBe(2) // Reviewed 2 and Recalled 2
    expect(screen.getByText('+20')).toBeInTheDocument() // +20 XP
  })
})
