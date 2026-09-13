import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConversationsPage } from '@/pages/ConversationsPage'
import { conversationsApi } from '@/api/conversations'
import {
  ConversationStartResponse,
  ConversationMessageResponse,
  ConversationEndResponse,
  ConversationSession,
} from '@/types'

vi.mock('@/api/conversations', () => ({
  conversationsApi: {
    start: vi.fn(),
    sendMessage: vi.fn(),
    end: vi.fn(),
    getById: vi.fn(),
    list: vi.fn(),
  },
}))

const mockStartResponse: ConversationStartResponse = {
  session_id: 'session-123',
  topic: 'Job Interview Preparation',
  initial_message: "Hello! Let's practice answering common interview questions today.",
  target_vocabulary: ['hesitate', 'confident', 'improve'],
}

const mockMessageResponse: ConversationMessageResponse = {
  message_id: 'msg-user-1',
  response: "That's a very honest answer! How do you work on improving when you notice hesitation?",
  vocabulary_detected: ['hesitate'],
  vocabulary_used: ['hesitate'],
}

const mockEndResponse: ConversationEndResponse = {
  session_id: 'session-123',
  status: 'ended',
  xp_earned: 20,
  evaluation: {
    vocabulary_used: ['hesitate', 'confident'],
    vocabulary_missed: ['improve'],
    usage_quality: {
      hesitate: 9.0,
      confident: 8.5,
    },
    overall_fluency: 8.5,
    feedback: 'Great conversation! You communicated your ideas clearly and used the target words naturally.',
    vocabulary_details: [
      {
        word: 'hesitate',
        used: true,
        quality: 9.0,
        context: 'I hesitate sometimes',
      },
      {
        word: 'confident',
        used: true,
        quality: 8.5,
        context: 'I feel confident',
      },
      {
        word: 'improve',
        used: false,
        quality: undefined,
        context: undefined,
      },
    ],
  },
}

const mockExistingSession: ConversationSession = {
  id: 'session-456',
  topic: 'Travel in Japan',
  target_vocabulary: ['adventure', 'explore'],
  vocabulary_used: ['adventure'],
  vocabulary_usage_count: 1,
  status: 'ended',
  message_count: 2,
  started_at: '2026-03-09T10:00:00Z',
  ended_at: '2026-03-09T10:15:00Z',
  messages: [
    {
      id: 'm1',
      role: 'assistant',
      content: 'Where in Japan would you love to explore?',
      vocabulary_detected: [],
      order_index: 1,
      created_at: '2026-03-09T10:00:00Z',
    },
    {
      id: 'm2',
      role: 'user',
      content: 'I want to go on a big mountain adventure in Hokkaido.',
      vocabulary_detected: ['adventure'],
      order_index: 2,
      created_at: '2026-03-09T10:02:00Z',
    },
  ],
  evaluation: {
    vocabulary_used: ['adventure'],
    vocabulary_missed: ['explore'],
    usage_quality: { adventure: 9.0 },
    overall_fluency: 8.0,
    feedback: 'Wonderful travel chat! You used adventure in a great context.',
  },
}

function renderConversationsPage(initialRoute = '/conversations') {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/conversations" element={<ConversationsPage />} />
          <Route path="/conversations/:id" element={<ConversationsPage />} />
          <Route path="/vocabulary" element={<div>Vocabulary Page Mock</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ConversationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders conversation start screen with topic input and suggestion chips', () => {
    renderConversationsPage()

    expect(screen.getByText(/ai conversation coach/i)).toBeInTheDocument()
    expect(screen.getByText(/start a new conversation/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/e.g., job interview/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start conversation/i })).toBeInTheDocument()
    expect(screen.getByText(/job interview preparation/i)).toBeInTheDocument()
  })

  it('starts a conversation and displays opening message and target vocabulary', async () => {
    const user = userEvent.setup()
    vi.mocked(conversationsApi.start).mockResolvedValueOnce(mockStartResponse)

    renderConversationsPage()

    const topicInput = screen.getByPlaceholderText(/e.g., job interview/i)
    await user.type(topicInput, 'Job Interview Preparation')

    const startBtn = screen.getByRole('button', { name: /start conversation/i })
    await user.click(startBtn)

    expect(conversationsApi.start).toHaveBeenCalledWith({
      topic: 'Job Interview Preparation',
      use_vocabulary: true,
    })

    await waitFor(() => {
      expect(screen.getByText(mockStartResponse.initial_message)).toBeInTheDocument()
    })

    expect(screen.getByText('Job Interview Preparation')).toBeInTheDocument()
    expect(screen.getByText('hesitate')).toBeInTheDocument()
    expect(screen.getByText('confident')).toBeInTheDocument()
    expect(screen.getByText('improve')).toBeInTheDocument()
  })

  it('allows user to send message and displays assistant response with detected vocabulary', async () => {
    const user = userEvent.setup()
    vi.mocked(conversationsApi.start).mockResolvedValueOnce(mockStartResponse)
    vi.mocked(conversationsApi.sendMessage).mockResolvedValueOnce(mockMessageResponse)

    renderConversationsPage()

    // Start session
    await user.click(screen.getByRole('button', { name: /start conversation/i }))

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/type your message in english/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/type your message in english/i)
    await user.type(input, 'I sometimes hesitate during behavioral questions.')

    const sendBtn = screen.getByRole('button', { name: /send/i })
    await user.click(sendBtn)

    expect(conversationsApi.sendMessage).toHaveBeenCalledWith(
      'session-123',
      'I sometimes hesitate during behavioral questions.'
    )

    await waitFor(() => {
      expect(screen.getByText(mockMessageResponse.response)).toBeInTheDocument()
    })

    // Verify user bubble & detected vocabulary chip
    expect(screen.getByText('I sometimes hesitate during behavioral questions.')).toBeInTheDocument()
    expect(screen.getByText(/used:/i)).toBeInTheDocument()
  })

  it('allows user to end conversation and renders complete evaluation card', async () => {
    const user = userEvent.setup()
    vi.mocked(conversationsApi.start).mockResolvedValueOnce(mockStartResponse)
    vi.mocked(conversationsApi.end).mockResolvedValueOnce(mockEndResponse)

    renderConversationsPage()

    // Start session
    await user.click(screen.getByRole('button', { name: /start conversation/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end & evaluate/i })).toBeInTheDocument()
    })

    // End session
    await user.click(screen.getByRole('button', { name: /end & evaluate/i }))

    expect(conversationsApi.end).toHaveBeenCalledWith('session-123')

    await waitFor(() => {
      expect(screen.getByText(/conversation evaluation/i)).toBeInTheDocument()
    })

    expect(screen.getByText('+20 XP Earned!')).toBeInTheDocument()
    expect(screen.getAllByText('8.5').length).toBeGreaterThanOrEqual(1) // Fluency & Quality score
    expect(screen.getByText(/words used \(2\)/i)).toBeInTheDocument()
    expect(screen.getByText(/words missed \(1\)/i)).toBeInTheDocument()
    expect(screen.getByText(mockEndResponse.evaluation.feedback)).toBeInTheDocument()
  })

  it('loads existing completed conversation when navigated with ID param', async () => {
    vi.mocked(conversationsApi.getById).mockResolvedValueOnce(mockExistingSession)

    renderConversationsPage('/conversations/session-456')

    await waitFor(() => {
      expect(screen.getByText('Travel in Japan')).toBeInTheDocument()
    })

    expect(screen.getByText('Where in Japan would you love to explore?')).toBeInTheDocument()
    expect(screen.getByText('I want to go on a big mountain adventure in Hokkaido.')).toBeInTheDocument()
    expect(screen.getByText(/conversation evaluation/i)).toBeInTheDocument()
    expect(screen.getByText(mockExistingSession.evaluation!.feedback)).toBeInTheDocument()
  })

  it('switches to history tab and lists past sessions', async () => {
    const user = userEvent.setup()
    vi.mocked(conversationsApi.list).mockResolvedValueOnce({
      items: [mockExistingSession],
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    })

    renderConversationsPage()

    const historyTabBtn = screen.getByRole('button', { name: /past chats/i })
    await user.click(historyTabBtn)

    expect(conversationsApi.list).toHaveBeenCalledWith(1, 20)

    await waitFor(() => {
      expect(screen.getByText('Travel in Japan')).toBeInTheDocument()
    })

    expect(screen.getByText(/completed/i)).toBeInTheDocument()
    expect(screen.getByText(/1 words used/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /view transcript/i })).toBeInTheDocument()
  })
})
