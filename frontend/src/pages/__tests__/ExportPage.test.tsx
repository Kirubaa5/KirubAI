import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ExportPage } from '@/pages/ExportPage'
import { exportApi } from '@/api/export'
import { ExportPreviewResponse } from '@/types'

vi.mock('@/api/export', () => ({
  exportApi: {
    getPreview: vi.fn(),
    download: vi.fn(),
  },
}))

const mockPreviewData: ExportPreviewResponse = {
  total_vocabulary_count: 15,
  matching_words_count: 12,
  status_distribution: {
    practiced: 5,
    mastered: 4,
    struggling: 3,
  },
  cefr_distribution: {
    B1: 6,
    B2: 4,
    C1: 2,
  },
  sample_words: ['hesitate', 'resilient', 'eloquent', 'ubiquitous'],
}

function renderExportPage() {
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
        <ExportPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ExportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the Export and Study Deck page with format choices and filters', async () => {
    vi.mocked(exportApi.getPreview).mockResolvedValueOnce(mockPreviewData)

    renderExportPage()

    expect(screen.getByText('Export & Study Deck Generator')).toBeInTheDocument()
    expect(screen.getByText('Anki Flashcard Deck')).toBeInTheDocument()
    expect(screen.getByText('CSV Spreadsheet')).toBeInTheDocument()
    expect(screen.getByText('JSON Data Archive')).toBeInTheDocument()
    expect(screen.getByText('2. Choose Vocabulary Filters')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText(/of 15 total/i)).toBeInTheDocument()
      expect(screen.getByText('hesitate')).toBeInTheDocument()
      expect(screen.getByText('resilient')).toBeInTheDocument()
    })
  })

  it('allows user to switch export format to CSV and JSON', async () => {
    const user = userEvent.setup()
    vi.mocked(exportApi.getPreview).mockResolvedValue(mockPreviewData)

    renderExportPage()

    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument()
    })

    // Click CSV
    const csvCard = screen.getByText('CSV Spreadsheet')
    await user.click(csvCard)

    expect(screen.getByRole('button', { name: /Download CSV Spreadsheet/i })).toBeInTheDocument()

    // Click JSON
    const jsonCard = screen.getByText('JSON Data Archive')
    await user.click(jsonCard)

    expect(screen.getByRole('button', { name: /Download JSON Data Archive/i })).toBeInTheDocument()
  })

  it('allows user to select different status and CEFR filters', async () => {
    const user = userEvent.setup()
    vi.mocked(exportApi.getPreview).mockResolvedValue(mockPreviewData)

    renderExportPage()

    await waitFor(() => {
      expect(screen.getByText('Active Learning')).toBeInTheDocument()
    })

    // Click Active Learning status filter
    await user.click(screen.getByText('Active Learning'))

    expect(exportApi.getPreview).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 'active',
      })
    )

    // Click B2 CEFR filter
    await user.click(screen.getByText('B2 - Upper Intermediate'))

    expect(exportApi.getPreview).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 'active',
        cefr_level: 'B2',
      })
    )
  })

  it('triggers download when download button is clicked and shows success feedback', async () => {
    const user = userEvent.setup()
    vi.mocked(exportApi.getPreview).mockResolvedValue(mockPreviewData)
    vi.mocked(exportApi.download).mockResolvedValueOnce({
      filename: 'kirubai_anki_deck_20260917.txt',
      success: true,
    })

    renderExportPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Download Anki Flashcard Deck/i })).toBeInTheDocument()
    })

    const downloadBtn = screen.getByRole('button', { name: /Download Anki Flashcard Deck/i })
    await user.click(downloadBtn)

    expect(exportApi.download).toHaveBeenCalledWith('anki', expect.any(Object))

    await waitFor(() => {
      expect(screen.getByText('Download Successful')).toBeInTheDocument()
      expect(screen.getByText(/Downloaded 12 words to kirubai_anki_deck_20260917.txt/i)).toBeInTheDocument()
    })
  })

  it('displays error message when download fails', async () => {
    const user = userEvent.setup()
    vi.mocked(exportApi.getPreview).mockResolvedValue(mockPreviewData)
    vi.mocked(exportApi.download).mockRejectedValueOnce(new Error('Export generation failed'))

    renderExportPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Download Anki Flashcard Deck/i })).toBeInTheDocument()
    })

    const downloadBtn = screen.getByRole('button', { name: /Download Anki Flashcard Deck/i })
    await user.click(downloadBtn)

    await waitFor(() => {
      expect(screen.getByText('Export Failed')).toBeInTheDocument()
      expect(screen.getByText('Export generation failed')).toBeInTheDocument()
    })
  })

  it('renders empty state and disables download button when 0 words match filters', async () => {
    vi.mocked(exportApi.getPreview).mockResolvedValueOnce({
      total_vocabulary_count: 10,
      matching_words_count: 0,
      status_distribution: {},
      cefr_distribution: {},
      sample_words: [],
    })

    renderExportPage()

    await waitFor(() => {
      expect(screen.getByText('No matching words')).toBeInTheDocument()
      expect(screen.getByText(/No vocabulary words match the selected filters/i)).toBeInTheDocument()
    })

    const downloadBtn = screen.getByRole('button', { name: /Download Anki Flashcard Deck \(0 words\)/i })
    expect(downloadBtn).toBeDisabled()
  })
})
