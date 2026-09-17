import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBreakdown } from '@/components/practice/ErrorBreakdown'
import { DiagnosticError } from '@/types'

describe('ErrorBreakdown Component', () => {
  const mockErrors: DiagnosticError[] = [
    {
      error_type: 'collocation',
      original_text: 'discuss about',
      explanation: "'Discuss' is a transitive verb that takes an object directly.",
      suggested_correction: 'discuss',
      severity: 'medium',
    },
    {
      error_type: 'grammar',
      original_text: 'look forward to meet',
      explanation: "Phrasal verb 'look forward to' requires a gerund (-ing form).",
      suggested_correction: 'look forward to meeting',
      severity: 'high',
    },
    {
      error_type: 'spelling',
      original_text: 'hestitate',
      explanation: "Misspelled verb: 'hesitate' is spelled with 'si'.",
      suggested_correction: 'hesitate',
      severity: 'low',
    },
  ]

  it('renders clean no-errors state when errors list is empty', () => {
    render(
      <ErrorBreakdown
        errors={[]}
        cefrLevel="B2"
        actionableTips={['Keep practicing advanced idioms.']}
      />
    )

    expect(screen.getByTestId('no-errors-state')).toBeInTheDocument()
    expect(screen.getByText('No Linguistic Errors Detected')).toBeInTheDocument()
    expect(screen.getByText('CEFR B2')).toBeInTheDocument()
    expect(screen.getByText('Keep practicing advanced idioms.')).toBeInTheDocument()
  })

  it('renders error list with type badges, spans, explanations, and corrections', () => {
    render(
      <ErrorBreakdown
        errors={mockErrors}
        cefrLevel="B1"
        actionableTips={['Review prepositional collocations.', 'Check gerund usage.']}
        userText="I look forward to meet you and will not hestitate to discuss about our project."
      />
    )

    expect(screen.getByTestId('errors-list')).toBeInTheDocument()
    expect(screen.getByText('3 diagnostic errors')).toBeInTheDocument()

    // Error Type Badges
    expect(screen.getByText('Collocation')).toBeInTheDocument()
    expect(screen.getByText('Grammar')).toBeInTheDocument()
    expect(screen.getByText('Spelling')).toBeInTheDocument()

    // Severity Badges
    expect(screen.getByText('High Severity')).toBeInTheDocument()
    expect(screen.getByText('Moderate')).toBeInTheDocument()
    expect(screen.getByText('Minor')).toBeInTheDocument()

    // Original Spans & Corrections
    expect(screen.getByText('"discuss about"')).toBeInTheDocument()
    expect(screen.getByText('"discuss"')).toBeInTheDocument()
    expect(screen.getByText('"look forward to meet"')).toBeInTheDocument()
    expect(screen.getByText('"look forward to meeting"')).toBeInTheDocument()

    // CEFR Level & Tips
    expect(screen.getByText('CEFR B1')).toBeInTheDocument()
    expect(screen.getByText('Review prepositional collocations.')).toBeInTheDocument()
    expect(screen.getByText('Check gerund usage.')).toBeInTheDocument()
  })

  it('highlights error spans in the user text', () => {
    const { container } = render(
      <ErrorBreakdown
        errors={mockErrors}
        userText="I look forward to meet you and will not hestitate to discuss about our project."
      />
    )

    const marks = container.querySelectorAll('mark')
    expect(marks.length).toBe(3)
    expect(marks[0].textContent).toBe('look forward to meet')
    expect(marks[1].textContent).toBe('hestitate')
    expect(marks[2].textContent).toBe('discuss about')
  })

  it('allows copying suggested correction', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    })

    render(<ErrorBreakdown errors={mockErrors} />)

    const copyButtons = screen.getAllByTitle('Copy correction')
    expect(copyButtons.length).toBe(3)

    fireEvent.click(copyButtons[0])
    expect(writeTextMock).toHaveBeenCalledWith('discuss')
  })

  it('handles undefined or null props gracefully without crashing', () => {
    render(<ErrorBreakdown />)
    expect(screen.getByTestId('no-errors-state')).toBeInTheDocument()
  })
})
