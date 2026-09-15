import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { VocabularyPage } from '@/pages/VocabularyPage'
import { vocabularyApi } from '@/api/vocabulary'
import { reviewsApi } from '@/api/reviews'
import { VocabularyListResponse } from '@/types'

vi.mock('@/api/vocabulary', () => ({
  vocabularyApi: {
    list: vi.fn(),
    add: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/api/reviews', () => ({
  reviewsApi: {
    getDue: vi.fn(),
  },
}))

const mockVocabList: VocabularyListResponse = {
  items: [
    {
      id: 'vocab-1',
      word: 'hesitate',
      status: 'struggling',
      mastery_score: 0.2,
      practice_count: 3,
      successful_usage_count: 1,
      failed_recall_count: 2,
      review_interval_days: 1,
      created_at: '2026-09-10T10:45:47.379519Z',
    },
    {
      id: 'vocab-2',
      word: 'resilient',
      status: 'reinforced',
      mastery_score: 0.85,
      practice_count: 5,
      successful_usage_count: 4,
      failed_recall_count: 1,
      review_interval_days: 7,
      created_at: '2026-09-10T10:45:47.379519Z',
    },
  ],
  total: 2,
  page: 1,
  per_page: 50,
  pages: 1,
}

function renderVocabularyPage() {
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
        <VocabularyPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('VocabularyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders vocabulary items when loaded successfully', async () => {
    vi.mocked(vocabularyApi.list).mockResolvedValueOnce(mockVocabList)
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce({ due_count: 0, items: [] })

    renderVocabularyPage()

    await waitFor(() => {
      expect(screen.getByText('hesitate')).toBeInTheDocument()
      expect(screen.getByText('resilient')).toBeInTheDocument()
    })
  })

  it('renders error state when vocabulary API fails', async () => {
    vi.mocked(vocabularyApi.list).mockRejectedValueOnce(new Error('Network error'))
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce({ due_count: 0, items: [] })

    renderVocabularyPage()

    await waitFor(() => {
      expect(screen.getByText('Failed to load vocabulary')).toBeInTheDocument()
      expect(screen.getByText(/There was an error loading your vocabulary list/i)).toBeInTheDocument()
    })
  })

  it('allows user to open add word form and submit a new word', async () => {
    const user = userEvent.setup()
    vi.mocked(vocabularyApi.list).mockResolvedValueOnce(mockVocabList)
    vi.mocked(reviewsApi.getDue).mockResolvedValueOnce({ due_count: 0, items: [] })
    vi.mocked(vocabularyApi.add).mockResolvedValueOnce({
      id: 'vocab-3',
      word: 'eloquent',
      status: 'new',
      mastery_score: 0.0,
      practice_count: 0,
      successful_usage_count: 0,
      failed_recall_count: 0,
      review_interval_days: 1,
      created_at: '2026-09-10T10:45:47.379519Z',
    })

    renderVocabularyPage()

    await waitFor(() => {
      expect(screen.getByText('Add New Word')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New Word'))

    const input = screen.getByPlaceholderText(/enter an english word/i)
    expect(input).toBeInTheDocument()

    await user.type(input, 'eloquent')
    await user.click(screen.getByRole('button', { name: 'Add Word' }))

    expect(vocabularyApi.add).toHaveBeenCalledWith('eloquent')
  })
})
