import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import {
  ConversationMessage,
  ConversationEvaluation,
  ConversationSession,
} from '@/types'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import {
  MessageSquare,
  Send,
  Sparkles,
  Award,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowLeft,
  Bot,
  User,
  History,
  Lightbulb,
} from 'lucide-react'

const SUGGESTED_TOPICS = [
  '💼 Job Interview Preparation',
  '✈️ Travel Adventures & Culture',
  '🤖 AI & Modern Technology',
  '🎨 Creative Hobbies & Passions',
  '🌱 Overcoming Daily Challenges',
]

export function ConversationsPage() {
  const { id: paramSessionId } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Tab mode: 'chat' or 'history'
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')

  // Start Form State
  const [topicInput, setTopicInput] = useState('')
  const [useVocab, setUseVocab] = useState(true)

  // Active Session State
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(paramSessionId || null)
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [targetVocabulary, setTargetVocabulary] = useState<string[]>([])
  const [vocabularyUsed, setVocabularyUsed] = useState<string[]>([])
  const [sessionTopic, setSessionTopic] = useState<string>('')
  const [userInput, setUserInput] = useState('')
  const [evaluation, setEvaluation] = useState<ConversationEvaluation | null>(null)
  const [isSessionEnded, setIsSessionEnded] = useState(false)
  const [xpEarned, setXpEarned] = useState<number | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  // Auto scroll to bottom of chat
  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Sync route param on direct navigation
  useEffect(() => {
    if (paramSessionId && paramSessionId !== currentSessionId) {
      setCurrentSessionId(paramSessionId)
    }
  }, [paramSessionId])

  // Fetch session details only on direct URL load or when messages are not yet loaded in state
  const shouldFetchSession = !!paramSessionId && messages.length === 0

  const {
    data: sessionData,
    isLoading: isLoadingSession,
    error: sessionFetchError,
  } = useQuery({
    queryKey: ['conversation-session', paramSessionId],
    queryFn: () => (paramSessionId ? conversationsApi.getById(paramSessionId) : null),
    enabled: shouldFetchSession,
  })

  useEffect(() => {
    if (sessionData) {
      setSessionTopic(sessionData.topic || 'English Conversation')
      setTargetVocabulary(sessionData.target_vocabulary || [])
      setVocabularyUsed(sessionData.vocabulary_used || [])
      setMessages(sessionData.messages || [])
      if (sessionData.status === 'ended') {
        setIsSessionEnded(true)
        if (sessionData.evaluation) {
          setEvaluation(sessionData.evaluation)
        }
      } else {
        setIsSessionEnded(false)
        setEvaluation(null)
      }
    }
  }, [sessionData])

  // Fetch conversation history list
  const {
    data: historyData,
    isLoading: isLoadingHistory,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['conversation-history'],
    queryFn: () => conversationsApi.list(1, 20),
    enabled: activeTab === 'history',
  })

  // Start Conversation Mutation
  const startMutation = useMutation({
    mutationFn: (topic: string) =>
      conversationsApi.start({
        topic: topic.trim() || undefined,
        use_vocabulary: useVocab,
      }),
    onSuccess: (data) => {
      setErrorMsg(null)
      setCurrentSessionId(data.session_id)
      setSessionTopic(data.topic)
      setTargetVocabulary(data.target_vocabulary || [])
      setVocabularyUsed([])
      setEvaluation(null)
      setIsSessionEnded(false)
      setXpEarned(null)
      setMessages([
        {
          id: 'init-msg',
          role: 'assistant',
          content: data.initial_message,
          vocabulary_detected: [],
          order_index: 1,
          created_at: new Date().toISOString(),
        },
      ])
      navigate(`/conversations/${data.session_id}`, { replace: true })
      queryClient.invalidateQueries({ queryKey: ['conversation-history'] })
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Failed to start conversation. Please try again.')
    },
  })

  // Send Message Mutation
  const sendMutation = useMutation({
    mutationFn: (content: string) => {
      if (!currentSessionId) throw new Error('No active session')
      return conversationsApi.sendMessage(currentSessionId, content)
    },
    onSuccess: (data, contentSent) => {
      setErrorMsg(null)
      // Update user message with detected vocabulary and append assistant response immutably
      const assistantMsg: ConversationMessage = {
        id: data.message_id || `asst-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        vocabulary_detected: [],
        order_index: messages.length + 1,
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => {
        const updated = prev.map((m) =>
          m.content === contentSent && m.role === 'user'
            ? { ...m, vocabulary_detected: data.vocabulary_detected }
            : m
        )
        return [...updated, assistantMsg]
      })
      setVocabularyUsed(data.vocabulary_used || [])
      queryClient.invalidateQueries({ queryKey: ['conversation-session', currentSessionId] })
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Failed to send message. Please try again.')
    },
  })

  // End Conversation Mutation
  const endMutation = useMutation({
    mutationFn: () => {
      if (!currentSessionId) throw new Error('No active session')
      return conversationsApi.end(currentSessionId)
    },
    onSuccess: (data) => {
      setErrorMsg(null)
      setIsSessionEnded(true)
      setEvaluation(data.evaluation)
      setXpEarned(data.xp_earned)
      queryClient.invalidateQueries({ queryKey: ['conversation-session', currentSessionId] })
      queryClient.invalidateQueries({ queryKey: ['conversation-history'] })
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
    },
    onError: (err: any) => {
      setErrorMsg(err?.response?.data?.detail || 'Failed to end conversation. Please try again.')
    },
  })

  // Handlers
  const handleStartConversation = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    startMutation.mutate(topicInput)
  }

  const handleSelectSuggestedTopic = (topic: string) => {
    const cleanTopic = topic.replace(/^[^\w\s]+/, '').trim()
    setTopicInput(cleanTopic)
    startMutation.mutate(cleanTopic)
  }

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = userInput.trim()
    if (!trimmed || sendMutation.isPending || isSessionEnded) return

    // Optimistically add user message
    const tempUserMsg: ConversationMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: trimmed,
      vocabulary_detected: [],
      order_index: messages.length + 1,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])
    setUserInput('')
    sendMutation.mutate(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(e)
    }
  }

  const handleResetToNew = () => {
    setCurrentSessionId(null)
    setMessages([])
    setEvaluation(null)
    setIsSessionEnded(false)
    setXpEarned(null)
    setTopicInput('')
    setErrorMsg(null)
    navigate('/conversations', { replace: true })
  }

  // Loading Session
  if (shouldFetchSession && isLoadingSession) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <LoadingSpinner size="lg" />
        <p className="text-sm text-gray-500">Loading conversation...</p>
      </div>
    )
  }

  if (shouldFetchSession && sessionFetchError) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorState
          title="Conversation Not Found"
          message="We couldn't load this conversation. It may not exist or belong to another account."
          onRetry={() => navigate('/conversations')}
        />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Header & Tab Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <MessageSquare className="h-7 w-7 text-indigo-600" />
            AI Conversation Coach
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            Practice natural English conversations and actively use your target vocabulary.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={activeTab === 'chat' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('chat')}
            className="flex items-center gap-1"
          >
            <Bot className="h-4 w-4" />
            Chat
          </Button>
          <Button
            variant={activeTab === 'history' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => {
              setActiveTab('history')
              refetchHistory()
            }}
            className="flex items-center gap-1"
          >
            <History className="h-4 w-4" />
            Past Chats
          </Button>
        </div>
      </div>

      {/* ERROR ALERT */}
      {errorMsg && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between text-red-700 text-sm">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="font-semibold text-red-800 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 1: CONVERSATION HISTORY */}
      {/* ============================================================ */}
      {activeTab === 'history' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <History className="h-5 w-5 text-indigo-600" />
              Conversation History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingHistory ? (
              <div className="py-12 flex flex-col items-center justify-center gap-3">
                <LoadingSpinner size="md" />
                <p className="text-sm text-gray-500">Loading history...</p>
              </div>
            ) : !historyData?.items || historyData.items.length === 0 ? (
              <div className="py-12 text-center text-gray-500">
                <MessageSquare className="h-10 w-10 mx-auto text-gray-400 mb-2" />
                <p className="font-medium text-gray-700">No conversations yet</p>
                <p className="text-sm mt-1">Start your first chat with the AI coach!</p>
                <Button size="sm" className="mt-4" onClick={() => setActiveTab('chat')}>
                  Start Chatting
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {historyData.items.map((session: ConversationSession) => (
                  <div
                    key={session.id}
                    className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:bg-gray-50 px-3 rounded-lg transition"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900">
                          {session.topic || 'General Conversation'}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            session.status === 'ended'
                              ? 'bg-gray-100 text-gray-700'
                              : 'bg-green-100 text-green-700'
                          }`}
                        >
                          {session.status === 'ended' ? 'Completed' : 'Active'}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {new Date(session.started_at).toLocaleDateString()}
                        </span>
                        <span>•</span>
                        <span>{session.message_count} messages</span>
                        <span>•</span>
                        <span className="text-indigo-600 font-medium">
                          {session.vocabulary_usage_count} words used
                        </span>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setCurrentSessionId(session.id)
                        setActiveTab('chat')
                        navigate(`/conversations/${session.id}`)
                      }}
                    >
                      {session.status === 'ended' ? 'View Transcript' : 'Continue Chat'}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ============================================================ */}
      {/* TAB 2: ACTIVE / START CONVERSATION */}
      {/* ============================================================ */}
      {activeTab === 'chat' && (
        <>
          {/* STATE A: START CONVERSATION VIEW */}
          {!currentSessionId && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Left 2 Cols: Setup Card */}
              <div className="md:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-indigo-600" />
                      Start a New Conversation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleStartConversation} className="space-y-5">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Conversation Topic (Optional)
                        </label>
                        <input
                          type="text"
                          value={topicInput}
                          onChange={(e) => setTopicInput(e.target.value)}
                          placeholder="e.g., Job Interview, Travel in Italy, Tech Trends..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Leave blank to get a randomly generated realistic scenario.
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="useVocabToggle"
                          checked={useVocab}
                          onChange={(e) => setUseVocab(e.target.checked)}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                        <label htmlFor="useVocabToggle" className="text-sm font-medium text-gray-700">
                          Practice with my active vocabulary words
                        </label>
                      </div>

                      <div>
                        <span className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                          Or Pick a Popular Topic:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {SUGGESTED_TOPICS.map((topic) => (
                            <button
                              key={topic}
                              type="button"
                              onClick={() => handleSelectSuggestedTopic(topic)}
                              className="text-xs px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium rounded-full border border-indigo-200 transition"
                            >
                              {topic}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="pt-2">
                        <Button
                          type="submit"
                          className="w-full sm:w-auto"
                          disabled={startMutation.isPending}
                        >
                          {startMutation.isPending ? 'Starting Conversation...' : 'Start Conversation'}
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </div>

              {/* Right Col: Tips Card */}
              <div>
                <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-100">
                  <CardHeader>
                    <CardTitle className="text-base text-indigo-900 flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-indigo-600" />
                      How it works
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-indigo-900 space-y-3">
                    <p>
                      <strong>1. Natural Chat:</strong> Your AI coach talks with you just like a friendly conversation partner.
                    </p>
                    <p>
                      <strong>2. Target Words:</strong> Try to naturally use the suggested vocabulary words in your replies.
                    </p>
                    <p>
                      <strong>3. Instant Feedback:</strong> The app detects your vocabulary in real-time and evaluates your fluency when you wrap up.
                    </p>
                    <p className="font-semibold text-indigo-800 flex items-center gap-1.5 pt-1">
                      <Award className="h-4 w-4 text-indigo-600" />
                      Earn +20 XP per session!
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* STATE B: ACTIVE / ENDED CONVERSATION VIEW */}
          {currentSessionId && (
            <div className="space-y-6">
              {/* Session Top Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleResetToNew}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    New Chat
                  </Button>
                  <div>
                    <h2 className="text-base font-bold text-gray-900">{sessionTopic}</h2>
                    <span className="text-xs text-gray-500">
                      {isSessionEnded ? 'Completed Session' : 'Active Conversation'}
                    </span>
                  </div>
                </div>

                {!isSessionEnded && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => endMutation.mutate()}
                    disabled={endMutation.isPending}
                    className="border-red-200 text-red-600 hover:bg-red-50"
                  >
                    {endMutation.isPending ? 'Ending...' : 'End & Evaluate'}
                  </Button>
                )}
              </div>

              {/* Target Vocabulary Chips Bar */}
              {targetVocabulary.length > 0 && (
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Target Vocabulary ({vocabularyUsed.length}/{targetVocabulary.length} used)
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {targetVocabulary.map((word) => {
                      const isUsed = vocabularyUsed.some(
                        (u) => u.toLowerCase() === word.toLowerCase()
                      )
                      return (
                        <span
                          key={word}
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition ${
                            isUsed
                              ? 'bg-green-50 text-green-700 border-green-300'
                              : 'bg-gray-50 text-gray-700 border-gray-200'
                          }`}
                        >
                          {isUsed ? (
                            <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                          ) : (
                            <span className="h-2 w-2 rounded-full bg-gray-400" />
                          )}
                          {word}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* EVALUATION RESULT BANNER (IF ENDED) */}
              {isSessionEnded && evaluation && (
                <Card className="border-2 border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white shadow-md">
                  <CardHeader className="pb-3 border-b border-indigo-100">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <Award className="h-6 w-6 text-indigo-600" />
                        Conversation Evaluation
                      </CardTitle>
                      {xpEarned !== null && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded-full border border-amber-300">
                          <Sparkles className="h-3.5 w-3.5 text-amber-600" />
                          +{xpEarned} XP Earned!
                        </span>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="pt-4 space-y-4">
                    {/* Fluency Meter */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4 bg-white p-4 rounded-lg border border-indigo-100">
                      <div className="flex-1">
                        <span className="text-xs font-semibold text-gray-500 uppercase">
                          Overall Fluency Score
                        </span>
                        <div className="flex items-baseline gap-2 mt-0.5">
                          <span className="text-2xl font-black text-indigo-600">
                            {evaluation.overall_fluency.toFixed(1)}
                          </span>
                          <span className="text-xs text-gray-500 font-medium">/ 10.0</span>
                        </div>
                      </div>

                      <div className="flex-2">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className="bg-indigo-600 h-2.5 rounded-full transition-all"
                            style={{ width: `${Math.min(100, evaluation.overall_fluency * 10)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Vocabulary Used vs Missed */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Words Used */}
                      <div className="bg-white p-3 rounded-lg border border-gray-200">
                        <span className="text-xs font-bold text-green-700 flex items-center gap-1 mb-2">
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                          Words Used ({evaluation.vocabulary_used.length})
                        </span>
                        {evaluation.vocabulary_used.length === 0 ? (
                          <p className="text-xs text-gray-500 italic">No target words used</p>
                        ) : (
                          <div className="flex flex-wrap gap-1.5">
                            {evaluation.vocabulary_used.map((word) => {
                              const quality = evaluation.usage_quality[word]
                              return (
                                <span
                                  key={word}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 text-green-800 text-xs font-medium rounded-md border border-green-200"
                                >
                                  {word}
                                  {quality && (
                                    <span className="text-[10px] bg-green-200 text-green-900 px-1 py-0.2 rounded font-bold">
                                      {quality.toFixed(1)}
                                    </span>
                                  )}
                                </span>
                              )
                            })}
                          </div>
                        )}
                      </div>

                      {/* Words Missed */}
                      <div className="bg-white p-3 rounded-lg border border-gray-200">
                        <span className="text-xs font-bold text-gray-600 flex items-center gap-1 mb-2">
                          <XCircle className="h-4 w-4 text-gray-400" />
                          Words Missed ({evaluation.vocabulary_missed.length})
                        </span>
                        {evaluation.vocabulary_missed.length === 0 ? (
                          <p className="text-xs text-green-600 font-medium">
                            Awesome! All target words were used!
                          </p>
                        ) : (
                          <div className="flex flex-wrap gap-1.5">
                            {evaluation.vocabulary_missed.map((word) => (
                              <span
                                key={word}
                                className="inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-md"
                              >
                                {word}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Coach Feedback */}
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <span className="text-xs font-semibold text-gray-500 uppercase block mb-1">
                        Coach Feedback
                      </span>
                      <p className="text-sm text-gray-800 leading-relaxed">
                        {evaluation.feedback}
                      </p>
                    </div>

                    {/* Next Step Action */}
                    <div className="flex flex-wrap items-center gap-3 pt-2">
                      <Button size="sm" onClick={handleResetToNew}>
                        Start Another Conversation
                      </Button>
                      <Link to="/vocabulary">
                        <Button size="sm" variant="outline">
                          View Vocabulary List
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Chat Transcript Area */}
              <Card className="overflow-hidden border border-gray-200 shadow-sm">
                <CardHeader className="bg-gray-50 py-3 px-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Conversation Transcript
                    </span>
                    <span className="text-xs text-gray-500">
                      {messages.length} messages
                    </span>
                  </div>
                </CardHeader>

                <CardContent className="p-4 space-y-4 max-h-[500px] overflow-y-auto bg-slate-50/50">
                  {messages.map((msg, idx) => {
                    const isAssistant = msg.role === 'assistant'
                    return (
                      <div
                        key={msg.id || idx}
                        className={`flex gap-3 ${isAssistant ? 'justify-start' : 'justify-end'}`}
                      >
                        {/* Assistant Avatar */}
                        {isAssistant && (
                          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-sm">
                            <Bot className="h-4 w-4" />
                          </div>
                        )}

                        {/* Message Bubble */}
                        <div
                          className={`max-w-[80%] sm:max-w-[70%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                            isAssistant
                              ? 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
                              : 'bg-indigo-600 text-white rounded-tr-none'
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{msg.content}</p>

                          {/* Detected Vocabulary Badge on User Message */}
                          {!isAssistant && msg.vocabulary_detected && msg.vocabulary_detected.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-indigo-400/50 flex flex-wrap items-center gap-1 text-[11px] text-indigo-100">
                              <Sparkles className="h-3 w-3 text-amber-300" />
                              <span>Used:</span>
                              {msg.vocabulary_detected.map((w) => (
                                <span
                                  key={w}
                                  className="font-bold bg-indigo-700/80 px-1.5 py-0.5 rounded text-white"
                                >
                                  {w}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* User Avatar */}
                        {!isAssistant && (
                          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 shrink-0 border border-indigo-200">
                            <User className="h-4 w-4" />
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {/* Typing Indicator */}
                  {sendMutation.isPending && (
                    <div className="flex gap-3 justify-start items-center">
                      <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none p-3 shadow-sm flex items-center gap-2 text-xs text-gray-500">
                        <LoadingSpinner size="sm" />
                        <span>AI Coach is thinking...</span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </CardContent>

                {/* Chat Input Footer */}
                {!isSessionEnded ? (
                  <div className="p-4 bg-white border-t border-gray-200">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                      <input
                        type="text"
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your message in English... (Press Enter to send)"
                        disabled={sendMutation.isPending}
                        className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                      />
                      <Button
                        type="submit"
                        disabled={!userInput.trim() || sendMutation.isPending}
                        className="flex items-center gap-1.5 px-4"
                      >
                        <Send className="h-4 w-4" />
                        <span className="hidden sm:inline">Send</span>
                      </Button>
                    </form>
                  </div>
                ) : (
                  <div className="p-4 bg-gray-50 border-t border-gray-200 text-center text-xs text-gray-500 font-medium">
                    This conversation has concluded. Start a new chat above!
                  </div>
                )}
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ConversationsPage
