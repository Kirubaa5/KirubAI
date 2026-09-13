import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { knowledgeApi } from '@/api/knowledge'
import {
  KnowledgeExplanationResponse,
  KnowledgeDocumentListResponse,
  KnowledgeDocument,
} from '@/types'

vi.mock('@/api/knowledge', () => ({
  knowledgeApi: {
    queryKnowledge: vi.fn(),
    getDocuments: vi.fn(),
    getCategories: vi.fn(),
    getDocumentById: vi.fn(),
  },
}))

const mockDocuments: KnowledgeDocument[] = [
  {
    id: 'DOC-GRAM-001',
    title: "Gerunds After Prepositional Phrasal Verbs ('Look forward to')",
    category: 'grammar',
    topic: "Verbs with Preposition 'to'",
    summary: "In expressions like 'look forward to', follow with a gerund (-ing) form.",
    content: 'Full content about gerunds and prepositional verbs...',
    tags: ['look forward to', 'gerund'],
    rules: ["Preposition 'to' + Gerund (-ing) or Noun Phrase"],
    correct_examples: ['I look forward to meeting you.'],
    common_mistakes: ["Incorrect: 'I look forward to meet you.'"],
    source: 'KirubAI Grammar Guide',
  },
  {
    id: 'DOC-COLL-001',
    title: "Collocations: 'Make' vs. 'Do' Core Distinctions",
    category: 'collocations',
    topic: 'Verb Collocations: Make vs Do',
    summary: "'Make' creates something new; 'do' performs a task or duty.",
    content: 'Full content about make vs do collocations...',
    tags: ['make', 'do', 'collocations'],
    rules: ['Make = Creation, Decision; Do = Tasks, Work'],
    correct_examples: ['Make a decision', 'Do homework'],
    common_mistakes: ["Incorrect: 'Do a decision'"],
    source: 'KirubAI Collocations Guide',
  },
]

const mockDocsResponse: KnowledgeDocumentListResponse = {
  items: mockDocuments,
  total: 2,
}

const mockExplanationResponse: KnowledgeExplanationResponse = {
  query: "Why is 'discuss about' incorrect?",
  category: 'grammar',
  summary: "'Discuss' is a transitive verb that directly takes an object without the preposition 'about'.",
  detailed_explanation: "'Discuss' already means 'to talk about'. Adding 'about' after 'discuss' is redundant.",
  rule_applied: 'Transitive Verb Direct Object Rule',
  correct_usage: ["Let's discuss the project milestones tomorrow."],
  incorrect_usage: ["'Let's discuss about the problem' (Incorrect: redundant preposition 'about')"],
  learning_tip: "Remember: 'Discuss = Talk about'. If you wouldn't say 'talk about about', don't say 'discuss about'!",
  groundedness_confidence: 0.98,
  sources: [
    {
      id: 'DOC-GRAM-002',
      title: "Transitive Verbs without Redundant Prepositions ('Discuss')",
      category: 'grammar',
      topic: 'Direct Transitive Verbs',
      relevance_score: 0.95,
      summary: "Transitive verbs take direct objects without 'about' or 'with'.",
      source: 'KirubAI Usage Reference',
    },
  ],
}

function renderKnowledgePage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/knowledge']}>
        <Routes>
          <Route path="/knowledge" element={<KnowledgePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('KnowledgePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders knowledge base header, search bar, and initial curated guides', async () => {
    vi.mocked(knowledgeApi.getDocuments).mockResolvedValueOnce(mockDocsResponse)

    renderKnowledgePage()

    await waitFor(() => {
      expect(screen.getByText(/grammar & usage knowledge base/i)).toBeInTheDocument()
      expect(screen.getByText(/gerunds after prepositional phrasal verbs/i)).toBeInTheDocument()
      expect(screen.getByText(/collocations: 'make' vs\. 'do'/i)).toBeInTheDocument()
    })

    expect(screen.getByPlaceholderText(/ask any grammar question/i)).toBeInTheDocument()
    expect(screen.getByText(/why is 'discuss about' incorrect\?/i)).toBeInTheDocument()
  })

  it('submits query and displays structured grounded explanation with rules and sources', async () => {
    const user = userEvent.setup()
    vi.mocked(knowledgeApi.getDocuments).mockResolvedValueOnce(mockDocsResponse)
    vi.mocked(knowledgeApi.queryKnowledge).mockResolvedValueOnce(mockExplanationResponse)

    renderKnowledgePage()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask any grammar question/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask any grammar question/i)
    await user.type(input, "Why is 'discuss about' incorrect?")

    const submitBtn = screen.getByRole('button', { name: /ask rag engine/i })
    await user.click(submitBtn)

    expect(knowledgeApi.queryKnowledge).toHaveBeenCalledWith({
      query: "Why is 'discuss about' incorrect?",
      category: undefined,
      top_k: 3,
    })

    await waitFor(() => {
      expect(
        screen.getByText(/'discuss' is a transitive verb that directly takes an object/i)
      ).toBeInTheDocument()
    })

    expect(screen.getByText(/rule: transitive verb direct object rule/i)).toBeInTheDocument()
    expect(screen.getByText(/grounded \(98%\)/i)).toBeInTheDocument()
    expect(screen.getByText(/correct usage & examples/i)).toBeInTheDocument()
    expect(screen.getByText(/common mistakes to avoid/i)).toBeInTheDocument()
    expect(screen.getByText(/remember: 'discuss = talk about'/i)).toBeInTheDocument()
    expect(screen.getByText('DOC-GRAM-002')).toBeInTheDocument()
  })

  it('opens guide detail modal when clicking a guide card', async () => {
    const user = userEvent.setup()
    vi.mocked(knowledgeApi.getDocuments).mockResolvedValueOnce(mockDocsResponse)

    renderKnowledgePage()

    await waitFor(() => {
      expect(screen.getByText(/collocations: 'make' vs\. 'do'/i)).toBeInTheDocument()
    })

    const guideCard = screen.getByText(/collocations: 'make' vs\. 'do'/i)
    await user.click(guideCard)

    await waitFor(() => {
      expect(screen.getByText(/full content about make vs do collocations/i)).toBeInTheDocument()
    })

    const closeBtn = screen.getByRole('button', { name: /close guide/i })
    await user.click(closeBtn)

    await waitFor(() => {
      expect(screen.queryByText(/full content about make vs do collocations/i)).not.toBeInTheDocument()
    })
  })

  it('renders error state when document fetching fails and allows retry', async () => {
    vi.mocked(knowledgeApi.getDocuments).mockRejectedValueOnce(new Error('Network error'))

    renderKnowledgePage()

    await waitFor(() => {
      expect(screen.getByText(/failed to load knowledge guides/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })
})
