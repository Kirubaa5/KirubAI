import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { practiceApi } from '@/api/practice'
import { vocabularyApi } from '@/api/vocabulary'
import { Scenario, PracticeSubmitResponse } from '@/types'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  MessageSquare,
  HelpCircle,
  Award,
  BookOpen,
  ArrowRight,
  Copy,
  Check,
} from 'lucide-react'

export function PracticePage() {
  const { id: vocabId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // State
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [targetWord, setTargetWord] = useState<string>('')
  const [currentScenario, setCurrentScenario] = useState<Scenario | null>(null)
  const [userResponse, setUserResponse] = useState('')
  const [lastSubmission, setLastSubmission] = useState<PracticeSubmitResponse | null>(null)
  const [copied, setCopied] = useState(false)
  const [inputError, setInputError] = useState<string | null>(null)

  // Fetch word info if needed for headers
  const { data: vocabData } = useQuery({
    queryKey: ['vocabulary-item', vocabId],
    queryFn: () => vocabularyApi.get(vocabId!),
    enabled: !!vocabId,
  })

  // Start Practice Session Mutation
  const startSessionMutation = useMutation({
    mutationFn: (vId: string) => practiceApi.start(vId),
    onSuccess: (data) => {
      setSessionId(data.session_id)
      setTargetWord(data.target_word)
      setCurrentScenario(data.scenario)
      setLastSubmission(null)
      setUserResponse('')
      setInputError(null)
    },
  })

  // Generate New Scenario Mutation
  const nextScenarioMutation = useMutation({
    mutationFn: (sId: string) => practiceApi.getScenario(sId),
    onSuccess: (newScenario) => {
      setCurrentScenario(newScenario)
      setLastSubmission(null)
      setUserResponse('')
      setInputError(null)
    },
  })

  // Submit Practice Attempt Mutation
  const submitAttemptMutation = useMutation({
    mutationFn: ({ sId, scenText, resp }: { sId: string; scenText: string; resp: string }) =>
      practiceApi.submit(sId, scenText, resp),
    onSuccess: (data) => {
      setLastSubmission(data)
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
      queryClient.invalidateQueries({ queryKey: ['vocabulary-item', vocabId] })
      queryClient.invalidateQueries({ queryKey: ['practice-session', sessionId] })
    },
  })

  // Complete Session Mutation
  const completeSessionMutation = useMutation({
    mutationFn: (sId: string) => practiceApi.complete(sId),
    onSuccess: () => {
      navigate('/vocabulary')
    },
  })

  const { mutate: startSession, isPending: isStarting, isSuccess: isStarted } = startSessionMutation

  // Initialize session on mount
  useEffect(() => {
    if (vocabId && !sessionId && !isStarting && !isStarted) {
      startSession(vocabId)
    }
  }, [vocabId, sessionId, isStarting, isStarted, startSession])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!sessionId || !currentScenario) return

    const trimmed = userResponse.trim()
    if (!trimmed) {
      setInputError('Please write a response before submitting.')
      return
    }

    setInputError(null)
    submitAttemptMutation.mutate({
      sId: sessionId,
      scenText: currentScenario.situation,
      resp: trimmed,
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  const handleCopyImproved = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRetryScenario = () => {
    setLastSubmission(null)
    setUserResponse('')
    setInputError(null)
  }

  const handleNextScenario = () => {
    if (sessionId) {
      nextScenarioMutation.mutate(sessionId)
    }
  }

  // Loading start state
  if (startSessionMutation.isPending || (!sessionId && !startSessionMutation.isError)) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="text-center max-w-md">
          <LoadingSpinner size="lg" className="mx-auto mb-4 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Preparing Practice Session</h2>
          <p className="text-sm text-gray-600">
            Crafting a realistic scenario for{' '}
            <span className="font-semibold text-blue-600">
              {vocabData?.word || 'your target word'}
            </span>
            ...
          </p>
        </div>
      </div>
    )
  }

  // Error starting session
  if (startSessionMutation.isError || !currentScenario) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <Link
            to="/vocabulary"
            className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Vocabulary
          </Link>
          <ErrorState
            title="Failed to start practice session"
            message="We could not generate a practice scenario. Please check your connection and try again."
            onRetry={() => vocabId && startSessionMutation.mutate(vocabId)}
          />
        </div>
      </div>
    )
  }

  const activeWord = targetWord || vocabData?.word || ''

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Navigation */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <Link
              to="/vocabulary"
              className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-1.5" />
              Vocabulary
            </Link>
            {vocabId && (
              <Link
                to={`/vocabulary/${vocabId}/learn`}
                className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
              >
                <BookOpen className="h-4 w-4 mr-1.5" />
                Word Details
              </Link>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-100 text-blue-800">
              Practice Mode
            </span>
            {vocabData?.details?.cefr_level && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                CEFR {vocabData.details.cefr_level}
              </span>
            )}
          </div>
        </div>

        {/* Word Header Card */}
        <Card className="mb-6 border-blue-100 bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-white shadow-sm">
          <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 capitalize">
                  {activeWord}
                </h1>
                {vocabData?.details?.pronunciation_text && (
                  <span className="text-sm font-mono text-gray-500 bg-white/80 px-2.5 py-0.5 rounded border border-gray-200">
                    /{vocabData.details.pronunciation_text}/
                  </span>
                )}
              </div>
              <p className="text-xs sm:text-sm text-gray-600 mt-1">
                {vocabData?.details?.simple_meaning ||
                  'Construct a natural response using this target word in the scenario below.'}
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-center">
              <span className="text-xs text-gray-500 font-medium">Target Word:</span>
              <span className="px-3 py-1 bg-blue-600 text-white font-bold text-sm rounded-lg shadow-sm">
                {activeWord}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Scenario Card */}
        <Card className="mb-6 border-gray-200 shadow-sm bg-white overflow-hidden">
          <CardHeader className="bg-gray-50/80 border-b border-gray-100 py-3.5 px-6">
            <CardTitle className="text-sm font-bold text-gray-800 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-blue-600" />
              Real-Life Scenario
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 block mb-1">
                The Situation
              </span>
              <p className="text-base sm:text-lg text-gray-900 font-medium leading-relaxed">
                {currentScenario.situation}
              </p>
            </div>

            <div className="bg-blue-50/80 border border-blue-100 rounded-xl p-4">
              <div className="flex items-start gap-2.5">
                <Sparkles className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-blue-900 block mb-0.5">Your Goal:</span>
                  <p className="text-sm text-blue-950 font-normal">{currentScenario.prompt}</p>
                </div>
              </div>
            </div>

            {currentScenario.context_hint && (
              <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50/70 border border-amber-200/80 rounded-lg p-3">
                <HelpCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Context Nuance Hint: </span>
                  <span>{currentScenario.context_hint}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submitting / Evaluating Animation State */}
        {submitAttemptMutation.isPending && (
          <Card className="mb-6 border-blue-200 bg-white shadow-sm p-8 text-center animate-pulse">
            <LoadingSpinner size="lg" className="mx-auto mb-4 text-blue-600" />
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              AI Linguistic Engine is Evaluating...
            </h3>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              Analyzing vocabulary usage accuracy, grammatical syntax, context alignment, and
              natural conversational fluency...
            </p>
          </Card>
        )}

        {/* Answer Input Card (Hidden when evaluation result is shown) */}
        {!lastSubmission && !submitAttemptMutation.isPending && (
          <Card className="mb-6 border-gray-200 shadow-sm bg-white">
            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label
                      htmlFor="user-response-input"
                      className="text-sm font-bold text-gray-900 flex items-center gap-1.5"
                    >
                      Your Response
                      <span className="text-xs font-normal text-gray-500">
                        (Include <span className="font-semibold text-blue-600">"{activeWord}"</span>)
                      </span>
                    </label>
                    <span className="text-xs text-gray-400 font-mono">
                      {userResponse.length} characters
                    </span>
                  </div>

                  <textarea
                    id="user-response-input"
                    rows={4}
                    value={userResponse}
                    onChange={(e) => {
                      setUserResponse(e.target.value)
                      if (inputError) setInputError(null)
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder={`Type how you would respond naturally in this situation using "${activeWord}"...`}
                    className="w-full rounded-lg border border-gray-300 p-3.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all shadow-inner"
                    autoFocus
                  />
                  {inputError && (
                    <p className="text-xs text-red-600 mt-1.5 flex items-center gap-1">
                      <AlertCircle className="h-3.5 w-3.5" />
                      {inputError}
                    </p>
                  )}
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                  <span className="text-[11px] text-gray-400 hidden sm:inline">
                    Tip: Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border">Ctrl</kbd> +{' '}
                    <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border">Enter</kbd> to submit
                  </span>

                  <div className="flex items-center gap-2.5 w-full sm:w-auto">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleNextScenario}
                      disabled={nextScenarioMutation.isPending}
                      className="flex items-center gap-1.5 text-gray-600"
                    >
                      <RefreshCw
                        className={`h-3.5 w-3.5 ${nextScenarioMutation.isPending ? 'animate-spin' : ''}`}
                      />
                      New Scenario
                    </Button>

                    <Button
                      type="submit"
                      disabled={!userResponse.trim()}
                      className="w-full sm:w-auto flex items-center justify-center gap-2"
                    >
                      <Send className="h-4 w-4" />
                      Submit & Evaluate
                    </Button>
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Evaluation Result View */}
        {lastSubmission && !submitAttemptMutation.isPending && (
          <div className="space-y-6">
            {/* Score Hero */}
            <Card
              className={`border overflow-hidden shadow-sm ${
                lastSubmission.is_successful
                  ? 'border-emerald-200 bg-gradient-to-br from-emerald-50/80 via-white to-white'
                  : 'border-amber-200 bg-gradient-to-br from-amber-50/80 via-white to-white'
              }`}
            >
              <div className="p-6 sm:p-8">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div className="flex items-start gap-3">
                    {lastSubmission.is_successful ? (
                      <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-full">
                        <CheckCircle2 className="h-6 w-6" />
                      </div>
                    ) : (
                      <div className="p-2.5 bg-amber-100 text-amber-700 rounded-full">
                        <AlertCircle className="h-6 w-6" />
                      </div>
                    )}
                    <div>
                      <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900">
                        {lastSubmission.is_successful
                          ? 'Great Attempt! Word Practiced Successfully'
                          : 'Good Effort! Keep Practicing'}
                      </h2>
                      <p className="text-xs sm:text-sm text-gray-600 mt-1">
                        {lastSubmission.is_successful
                          ? `You earned +15 XP and progressed "${activeWord}" toward active mastery.`
                          : `Earned +5 XP for this attempt. Review the suggestions below and try again!`}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col items-center justify-center px-4 py-2 bg-white rounded-xl border border-gray-200 shadow-sm shrink-0">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                      Overall Score
                    </span>
                    <span
                      className={`text-2xl sm:text-3xl font-black ${
                        lastSubmission.scores.overall >= 8.0
                          ? 'text-emerald-600'
                          : lastSubmission.scores.overall >= 6.0
                          ? 'text-blue-600'
                          : 'text-amber-600'
                      }`}
                    >
                      {lastSubmission.scores.overall.toFixed(1)}{' '}
                      <span className="text-xs text-gray-400 font-normal">/ 10</span>
                    </span>
                  </div>
                </div>

                {/* 4 Dimension Score Bars */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-4 border-t border-gray-100">
                  {/* Vocabulary Usage */}
                  <div className="bg-white rounded-lg p-3.5 border border-gray-200/80 shadow-xs">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-gray-700">Vocabulary</span>
                      <span className="text-xs font-bold text-gray-900 font-mono">
                        {lastSubmission.scores.vocabulary_usage.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          lastSubmission.scores.vocabulary_usage >= 6.0
                            ? 'bg-blue-600'
                            : 'bg-amber-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, lastSubmission.scores.vocabulary_usage * 10)
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 mt-1 block">Weight: 30%</span>
                  </div>

                  {/* Grammar */}
                  <div className="bg-white rounded-lg p-3.5 border border-gray-200/80 shadow-xs">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-gray-700">Grammar</span>
                      <span className="text-xs font-bold text-gray-900 font-mono">
                        {lastSubmission.scores.grammar.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          lastSubmission.scores.grammar >= 6.0 ? 'bg-indigo-600' : 'bg-amber-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, lastSubmission.scores.grammar * 10)
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 mt-1 block">Weight: 20%</span>
                  </div>

                  {/* Context */}
                  <div className="bg-white rounded-lg p-3.5 border border-gray-200/80 shadow-xs">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-gray-700">Context Fit</span>
                      <span className="text-xs font-bold text-gray-900 font-mono">
                        {lastSubmission.scores.context.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          lastSubmission.scores.context >= 6.0 ? 'bg-emerald-600' : 'bg-amber-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, lastSubmission.scores.context * 10)
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 mt-1 block">Weight: 25%</span>
                  </div>

                  {/* Naturalness */}
                  <div className="bg-white rounded-lg p-3.5 border border-gray-200/80 shadow-xs">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-gray-700">Naturalness</span>
                      <span className="text-xs font-bold text-gray-900 font-mono">
                        {lastSubmission.scores.naturalness.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          lastSubmission.scores.naturalness >= 6.0
                            ? 'bg-purple-600'
                            : 'bg-amber-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, lastSubmission.scores.naturalness * 10)
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-400 mt-1 block">Weight: 25%</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* User Attempt vs AI Feedback */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* User Response */}
              <Card className="border-gray-200 shadow-sm bg-white">
                <CardHeader className="pb-3 border-b border-gray-100">
                  <CardTitle className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-gray-500" />
                    What You Said
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-sm text-gray-800 leading-relaxed italic bg-gray-50 p-3.5 rounded-lg border border-gray-200/60">
                    "{lastSubmission.user_response}"
                  </p>
                </CardContent>
              </Card>

              {/* Constructive AI Feedback */}
              <Card className="border-blue-100 shadow-sm bg-white">
                <CardHeader className="pb-3 border-b border-blue-50 bg-blue-50/30">
                  <CardTitle className="text-sm font-bold text-blue-900 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-blue-600" />
                    AI Constructive Feedback
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-sm text-gray-800 leading-relaxed">
                    {lastSubmission.feedback}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Native Speaker Alternative */}
            {lastSubmission.improved_version && (
              <Card className="border-emerald-200 bg-emerald-50/40 shadow-sm overflow-hidden">
                <CardHeader className="pb-2 border-b border-emerald-100 bg-emerald-50/60">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-bold text-emerald-950 flex items-center gap-2">
                      <Award className="h-4 w-4 text-emerald-700" />
                      More Natural / Native-Speaker Phrasing
                    </CardTitle>
                    <button
                      onClick={() => handleCopyImproved(lastSubmission.improved_version!)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-emerald-800 hover:text-emerald-950 p-1 rounded transition-colors"
                      title="Copy to clipboard"
                    >
                      {copied ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-600" /> Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" /> Copy
                        </>
                      )}
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-sm sm:text-base font-medium text-emerald-950 leading-relaxed">
                    "{lastSubmission.improved_version}"
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Action Bar */}
            <Card className="border-gray-200 bg-white shadow-sm">
              <CardContent className="p-4 sm:p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <Button
                    variant="outline"
                    onClick={handleRetryScenario}
                    className="w-full sm:w-auto flex items-center justify-center gap-1.5"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Retry This Scenario
                  </Button>
                  <Button
                    onClick={handleNextScenario}
                    disabled={nextScenarioMutation.isPending}
                    className="w-full sm:w-auto flex items-center justify-center gap-1.5"
                  >
                    {nextScenarioMutation.isPending ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <>
                        <span>Next Scenario</span>
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => sessionId && completeSessionMutation.mutate(sessionId)}
                    className="text-gray-500 hover:text-gray-900"
                  >
                    Finish Session
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

export default PracticePage
